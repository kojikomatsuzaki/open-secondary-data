#!/usr/bin/env python3

"""
文部科学省「学校コード」の最新CSVを取得する。

文部科学省の学校コード公開ページから、
「最新の学校コード一覧」に掲載されているCSVファイルを検出し、
本データセットの sources/ ディレクトリへ保存する。

Primary source:
https://www.mext.go.jp/b_menu/toukei/mext_01087.html
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag


# ==========================================
# Configuration
# ==========================================

MEXT_SCHOOL_CODES_PAGE_URL = (
    "https://www.mext.go.jp/b_menu/toukei/mext_01087.html"
)

REQUEST_TIMEOUT_SECONDS = 30

# 現在の文科省公開形式では、
# 「一般学校・東日本」「大学等・全国」「一般学校・西日本」の3CSV。
#
# 件数が変化した場合は、文科省側の公開構造が変更された可能性があるため、
# 自動的に処理を続けず人間による確認を要求する。
EXPECTED_CSV_COUNT = 3


# ==========================================
# Paths
# ==========================================

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
DATASET_DIRECTORY = SCRIPT_DIRECTORY.parent
SOURCES_DIRECTORY = DATASET_DIRECTORY / "sources"


# ==========================================
# HTTP
# ==========================================

def create_http_session() -> requests.Session:
    """
    文科省へのHTTPアクセスに使用するSessionを作成する。

    User-Agentを明示することで、
    公開サイトへアクセスする主体を可能な範囲で明確にする。
    """

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "open-secondary-data/1.0 "
                "(https://github.com/kojikomatsuzaki/open-secondary-data)"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }
    )

    return session


# ==========================================
# Source Page
# ==========================================

def fetch_source_page(session: requests.Session) -> bytes:
    """
    文科省の学校コード公開ページをbytesとして取得する。

    response.textへ変換せずbytesのままBeautifulSoupへ渡すことで、
    HTML側の文字コード情報をBeautifulSoupに解釈させる。
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

    クエリ文字列が付与される可能性を考え、
    URL全体ではなくpath部分の拡張子を確認する。
    """

    parsed_url = urlparse(url)

    return parsed_url.path.lower().endswith(".csv")


def extract_latest_csv_urls(html: bytes) -> list[str]:
    """
    「最新の学校コード一覧」に掲載されたCSVだけを抽出する。

    文科省ページには過去年度のCSVも掲載されているため、
    ページ内のCSVリンクをすべて取得してはいけない。

    「最新の学校コード一覧」という文字列を起点として、
    「過去の学校コード一覧」が現れるまでDOMを順にたどる。
    """

    soup = BeautifulSoup(html, "html.parser")

    latest_marker = soup.find(
        string=lambda text: (
            text is not None
            and "最新の学校コード一覧" in text
        )
    )

    if latest_marker is None:
        raise RuntimeError(
            "文科省ページから"
            "「最新の学校コード一覧」を確認できませんでした。"
        )

    csv_urls: list[str] = []

    for element in latest_marker.next_elements:

        # 「過去の学校コード一覧」まで到達したら、
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
# ==========================================

def validate_csv_urls(csv_urls: list[str]) -> None:
    """
    文科省側の公開構造変更を検出する。

    想定外の件数になった場合に黙って処理を続けると、
    不完全な一次資料から二次データを生成する危険がある。

    そのため、安全側に倒して処理を停止する。
    """

    if len(csv_urls) != EXPECTED_CSV_COUNT:
        detected_urls = "\n".join(
            f"- {url}" for url in csv_urls
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
# Download
# ==========================================

def download_csv_files(
    session: requests.Session,
    csv_urls: list[str],
) -> list[Path]:
    """
    最新CSVをsources/へ保存する。

    文科省が付与したファイル名を変更せず保存することで、
    保存ファイルと一次情報源との対応関係を維持する。
    """

    SOURCES_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    downloaded_files: list[Path] = []

    for csv_url in csv_urls:
        filename = Path(
            urlparse(csv_url).path
        ).name

        destination = (
            SOURCES_DIRECTORY / filename
        )

        print(f"Downloading: {csv_url}")
        print(f"         -> {destination}")

        response = session.get(
            csv_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

        destination.write_bytes(
            response.content
        )

        downloaded_files.append(
            destination
        )

    return downloaded_files


# ==========================================
# Main
# ==========================================

def main() -> int:
    """
    文科省の最新版CSVを検出し、
    sources/へ保存する。
    """

    print("MEXT School Codes source fetcher")
    print("--------------------------------")
    print(
        f"Source page: "
        f"{MEXT_SCHOOL_CODES_PAGE_URL}"
    )
    print()

    try:
        session = create_http_session()

        html = fetch_source_page(session)

        csv_urls = extract_latest_csv_urls(
            html
        )

        validate_csv_urls(csv_urls)

        print(
            f"Found {len(csv_urls)} "
            "latest CSV files."
        )
        print()

        for csv_url in csv_urls:
            print(f"- {csv_url}")

        print()

        downloaded_files = (
            download_csv_files(
                session=session,
                csv_urls=csv_urls,
            )
        )

        print()
        print("Download completed.")

        for downloaded_file in downloaded_files:
            print(
                f"- {downloaded_file}"
            )

        return 0

    except requests.RequestException as error:
        print(
            f"HTTP error: {error}",
            file=sys.stderr,
        )
        return 1

    except RuntimeError as error:
        print(
            f"Validation error: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
