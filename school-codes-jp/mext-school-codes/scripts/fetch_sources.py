#!/usr/bin/env python3

"""
文部科学省「学校コード」の最新版CSVを確認し、
変更がある場合のみ sources/ を更新する。

Primary source:
https://www.mext.go.jp/b_menu/toukei/mext_01087.html

役割
----
1. 文部科学省の「最新の学校コード一覧」を確認する
2. 最新CSV 3ファイルを取得する
3. 現在の sources/*.csv と内容を比較する
4. 完全一致なら何も変更しない
5. 差異があれば、最新版3ファイルへ置き換える
6. GitHub Actionsでは changed=true/false を出力する

sources/ には常に現在の一次情報源だけを置く。
過去の一次情報源はGit履歴によって保存する。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag


# ==========================================
# Configuration
# 設定
# ==========================================

MEXT_SCHOOL_CODES_PAGE_URL = (
    "https://www.mext.go.jp/b_menu/toukei/mext_01087.html"
)

REQUEST_TIMEOUT_SECONDS = 30

# 現在の文科省公開形式では、
# 最新版は3つのCSVで構成されている。
#
# 件数が変化した場合は、自動的に処理を継続せず、
# 文科省側の公開構造変更として人間に確認を求める。
EXPECTED_CSV_COUNT = 3


# ==========================================
# Paths
# パス
# ==========================================

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
DATASET_DIRECTORY = SCRIPT_DIRECTORY.parent
SOURCES_DIRECTORY = DATASET_DIRECTORY / "sources"


# ==========================================
# Data Structures
# データ構造
# ==========================================

@dataclass(frozen=True)
class RemoteSourceFile:
    """
    文科省から取得した一次CSVを表す。

    ファイルをすべて正常に取得してから sources/ を変更するため、
    一度メモリ上に保持する。
    """

    url: str
    filename: str
    content: bytes


@dataclass(frozen=True)
class ChangeSummary:
    """
    現在の一次CSVと最新版CSVとの差分概要。
    """

    added: tuple[str, ...]
    removed: tuple[str, ...]
    modified: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(
            self.added
            or self.removed
            or self.modified
        )


# ==========================================
# HTTP
# HTTPアクセス
# ==========================================

def create_http_session() -> requests.Session:
    """
    文科省へのHTTPアクセスに使用するSessionを作成する。

    User-Agentを明示し、アクセス主体を可能な範囲で
    不透明にしないようにする。
    """

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "open-secondary-data/1.0 "
                "(https://github.com/"
                "kojikomatsuzaki/open-secondary-data)"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }
    )

    return session


# ==========================================
# Source Page
# 一次情報源ページ
# ==========================================

def fetch_source_page(
    session: requests.Session,
) -> bytes:
    """
    文科省の学校コード公開ページを取得する。

    bytesのままBeautifulSoupへ渡し、
    HTML側の文字コード情報を利用して解釈させる。
    """

    response = session.get(
        MEXT_SCHOOL_CODES_PAGE_URL,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    return response.content


def is_csv_url(url: str) -> bool:
    """
    URLがCSVファイルを指しているか確認する。
    """

    parsed_url = urlparse(url)

    return parsed_url.path.lower().endswith(
        ".csv"
    )


def extract_latest_csv_urls(
    html: bytes,
) -> list[str]:
    """
    「最新の学校コード一覧」に含まれるCSVだけを抽出する。

    文科省ページには過去版も掲載されているため、
    ページ内のCSVリンクすべてを取得してはいけない。
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    latest_marker = soup.find(
        string=lambda text: (
            text is not None
            and "最新の学校コード一覧" in text
        )
    )

    if latest_marker is None:
        raise RuntimeError(
            "文科省ページから"
            "「最新の学校コード一覧」を"
            "確認できませんでした。"
        )

    csv_urls: list[str] = []

    for element in latest_marker.next_elements:

        # 「過去の学校コード一覧」へ到達した時点で、
        # 最新版セクションの処理を終了する。
        if isinstance(element, str):
            if "過去の学校コード一覧" in element:
                break

        if not isinstance(element, Tag):
            continue

        if element.name != "a":
            continue

        href = element.get("href")

        if not href:
            continue

        csv_url = urljoin(
            MEXT_SCHOOL_CODES_PAGE_URL,
            href,
        )

        if not is_csv_url(csv_url):
            continue

        if csv_url not in csv_urls:
            csv_urls.append(csv_url)

    return csv_urls


# ==========================================
# Validation
# 文科省公開形式の検証
# ==========================================

def validate_csv_urls(
    csv_urls: list[str],
) -> None:
    """
    文科省側の公開構造変更を検出する。

    想定外のCSV件数になった場合は、
    不完全な一次情報源から二次データを生成しないよう
    安全側に倒して処理を停止する。
    """

    if len(csv_urls) == EXPECTED_CSV_COUNT:
        return

    detected_urls = "\n".join(
        f"- {url}"
        for url in csv_urls
    )

    raise RuntimeError(
        "最新版CSVの件数が想定と異なります。\n"
        f"想定: {EXPECTED_CSV_COUNT}件\n"
        f"検出: {len(csv_urls)}件\n"
        "\n"
        "検出したURL:\n"
        f"{detected_urls or '(none)'}\n"
        "\n"
        "文科省ページの構造または公開形式が"
        "変更された可能性があります。"
    )


# ==========================================
# Remote Files
# 最新一次CSVの取得
# ==========================================

def download_remote_source_files(
    session: requests.Session,
    csv_urls: list[str],
) -> list[RemoteSourceFile]:
    """
    最新CSVをすべてメモリ上へ取得する。

    sources/ を先に変更しないのは、
    3ファイルの途中で取得に失敗した場合に、
    ローカルの一次情報源を中途半端な状態にしないため。
    """

    remote_files: list[
        RemoteSourceFile
    ] = []

    for csv_url in csv_urls:

        filename = Path(
            urlparse(csv_url).path
        ).name

        print(
            f"Checking: {csv_url}"
        )

        response = session.get(
            csv_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

        remote_files.append(
            RemoteSourceFile(
                url=csv_url,
                filename=filename,
                content=response.content,
            )
        )

    return remote_files


# ==========================================
# Local Files
# 現在保存されている一次CSV
# ==========================================

def load_local_source_files() -> dict[str, bytes]:
    """
    現在の sources/*.csv を読み込む。

    key:
        filename

    value:
        raw bytes
    """

    if not SOURCES_DIRECTORY.exists():
        return {}

    local_files: dict[str, bytes] = {}

    for source_file in sorted(
        SOURCES_DIRECTORY.glob("*.csv")
    ):
        local_files[
            source_file.name
        ] = source_file.read_bytes()

    return local_files


# ==========================================
# Change Detection
# 更新判定
# ==========================================

def compare_source_files(
    local_files: dict[str, bytes],
    remote_files: list[RemoteSourceFile],
) -> ChangeSummary:
    """
    現在の一次CSVと文科省最新版を比較する。

    比較対象は、
    - ファイル名
    - ファイル内容そのもの

    URLやファイル名が同じでも内容が変更された場合を
    検出できるよう、bytes同士を直接比較する。
    """

    remote_by_filename = {
        remote_file.filename:
            remote_file.content
        for remote_file in remote_files
    }

    local_names = set(
        local_files.keys()
    )

    remote_names = set(
        remote_by_filename.keys()
    )

    added = tuple(
        sorted(
            remote_names - local_names
        )
    )

    removed = tuple(
        sorted(
            local_names - remote_names
        )
    )

    modified = tuple(
        sorted(
            filename
            for filename
            in local_names & remote_names
            if (
                local_files[filename]
                != remote_by_filename[filename]
            )
        )
    )

    return ChangeSummary(
        added=added,
        removed=removed,
        modified=modified,
    )


# ==========================================
# Source Replacement
# 一次CSVの置き換え
# ==========================================

def replace_local_source_files(
    remote_files: list[RemoteSourceFile],
) -> None:
    """
    sources/ を最新版CSVへ置き換える。

    過去版を同時に残すと normalize.py が複数版を
    一緒に読み込んでしまうため、working treeには
    カレント版だけを置く。

    過去版そのものはGit履歴によって保持される。
    """

    SOURCES_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    # すべてのremoteファイルが取得済みであることを確認してから
    # 現在のCSVを削除するため、途中失敗による半端な状態を避けられる。
    for existing_file in (
        SOURCES_DIRECTORY.glob("*.csv")
    ):
        existing_file.unlink()

    for remote_file in remote_files:

        destination = (
            SOURCES_DIRECTORY
            / remote_file.filename
        )

        destination.write_bytes(
            remote_file.content
        )

        print(
            f"Saved: {destination}"
        )


# ==========================================
# GitHub Actions Output
# GitHub Actionsへの結果通知
# ==========================================

def write_github_output(
    name: str,
    value: str,
) -> None:
    """
    GitHub Actions上で実行されている場合のみ、
    step output をGITHUB_OUTPUTへ書き込む。

    ローカル実行時には何もしない。
    """

    github_output = os.environ.get(
        "GITHUB_OUTPUT"
    )

    if not github_output:
        return

    with open(
        github_output,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            f"{name}={value}\n"
        )


def publish_change_outputs(
    summary: ChangeSummary,
) -> None:
    """
    後続のGitHub Actions stepから利用できるよう、
    更新判定結果を出力する。
    """

    write_github_output(
        "changed",
        (
            "true"
            if summary.changed
            else "false"
        ),
    )

    write_github_output(
        "added_count",
        str(len(summary.added)),
    )

    write_github_output(
        "removed_count",
        str(len(summary.removed)),
    )

    write_github_output(
        "modified_count",
        str(len(summary.modified)),
    )


# ==========================================
# Change Report
# 差分概要表示
# ==========================================

def print_change_summary(
    summary: ChangeSummary,
) -> None:
    """
    更新内容を人間がログから確認できる形で表示する。
    """

    print()
    print("Source comparison")
    print("-----------------")

    if not summary.changed:
        print(
            "No changes detected."
        )
        return

    if summary.added:
        print("Added:")
        for filename in summary.added:
            print(
                f"  + {filename}"
            )

    if summary.removed:
        print("Removed:")
        for filename in summary.removed:
            print(
                f"  - {filename}"
            )

    if summary.modified:
        print("Modified:")
        for filename in summary.modified:
            print(
                f"  * {filename}"
            )


# ==========================================
# Main
# メイン処理
# ==========================================

def main() -> int:
    """
    文科省最新版を確認し、
    必要な場合のみ sources/ を更新する。
    """

    print(
        "MEXT School Codes source checker"
    )
    print(
        "--------------------------------"
    )
    print(
        f"Source page: "
        f"{MEXT_SCHOOL_CODES_PAGE_URL}"
    )
    print()

    try:
        session = create_http_session()

        # ------------------------------------------
        # 1. Source page
        # ------------------------------------------

        html = fetch_source_page(
            session
        )

        csv_urls = extract_latest_csv_urls(
            html
        )

        validate_csv_urls(
            csv_urls
        )

        print(
            f"Found {len(csv_urls)} "
            "latest CSV files."
        )

        for csv_url in csv_urls:
            print(
                f"- {csv_url}"
            )

        print()

        # ------------------------------------------
        # 2. Download remote files into memory
        # ------------------------------------------

        remote_files = (
            download_remote_source_files(
                session=session,
                csv_urls=csv_urls,
            )
        )

        # ------------------------------------------
        # 3. Read current local files
        # ------------------------------------------

        local_files = (
            load_local_source_files()
        )

        print()
        print(
            f"Current local CSV files: "
            f"{len(local_files)}"
        )

        # ------------------------------------------
        # 4. Compare
        # ------------------------------------------

        summary = compare_source_files(
            local_files=local_files,
            remote_files=remote_files,
        )

        print_change_summary(
            summary
        )

        publish_change_outputs(
            summary
        )

        # ------------------------------------------
        # 5. No changes
        # ------------------------------------------

        if not summary.changed:
            print()
            print(
                "Current sources are already "
                "up to date."
            )

            return 0

        # ------------------------------------------
        # 6. Replace current sources
        # ------------------------------------------

        print()
        print(
            "Source changes detected."
        )
        print(
            "Replacing current source files..."
        )

        replace_local_source_files(
            remote_files
        )

        print()
        print(
            "Source files updated successfully."
        )

        return 0

    except requests.RequestException as error:
        print(
            f"HTTP error: {error}",
            file=sys.stderr,
        )

        return 1

    except (
        RuntimeError,
        OSError,
    ) as error:
        print(
            f"Error: {error}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
