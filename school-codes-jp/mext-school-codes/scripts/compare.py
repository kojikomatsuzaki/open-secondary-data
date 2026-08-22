#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compare previous and current normalized MEXT School Codes data.

GitのHEADにある前回版 schools.csv と、
working tree上の現在版 schools.csv を比較し、
人間がレビューしやすいMarkdown差分レポートを生成する。

Output:
    reports/latest-changes.md
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path
from typing import Any


# ==========================================
# Paths
# パス
# ==========================================

SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR.parent
REPOSITORY_ROOT = DATASET_DIR.parents[1]

CURRENT_CSV_PATH = DATASET_DIR / "data" / "schools.csv"
REPORTS_DIR = DATASET_DIR / "reports"
REPORT_PATH = REPORTS_DIR / "latest-changes.md"

REPOSITORY_RELATIVE_CSV_PATH = (
    "school-codes-jp/"
    "mext-school-codes/"
    "data/"
    "schools.csv"
)


# ==========================================
# Comparison Configuration
# 比較対象
# ==========================================

PRIMARY_KEY = "school_code"

COMPARISON_FIELDS = [
    "school_name",
    "school_type_code",
    "school_type_source_label",
    "school_type_name_ja",
    "school_type_name_en",
    "prefecture_code",
    "prefecture_name",
    "founder_code",
    "founder_source_label",
    "founder_name_ja",
    "founder_name_en",
    "school_status_code",
    "school_status_source_label",
    "school_status_name_ja",
    "school_status_name_en",
    "address",
    "postal_code",
    "attribute_set_date",
    "attribute_abolished_date",
    "obsolete_school_survey_number",
    "successor_school_code",
]

FIELD_LABELS_JA = {
    "school_name": "学校名",
    "school_type_code": "学校種コード",
    "school_type_source_label": "学校種・原表記",
    "school_type_name_ja": "学校種名",
    "school_type_name_en": "学校種名（英語）",
    "prefecture_code": "都道府県コード",
    "prefecture_name": "都道府県名",
    "founder_code": "設置区分コード",
    "founder_source_label": "設置区分・原表記",
    "founder_name_ja": "設置区分名",
    "founder_name_en": "設置区分名（英語）",
    "school_status_code": "本分校区分コード",
    "school_status_source_label": "本分校区分・原表記",
    "school_status_name_ja": "本分校区分名",
    "school_status_name_en": "本分校区分名（英語）",
    "address": "学校所在地",
    "postal_code": "郵便番号",
    "attribute_set_date": "属性情報設定年月日",
    "attribute_abolished_date": "属性情報廃止年月日",
    "obsolete_school_survey_number": "旧学校調査番号",
    "successor_school_code": "移行後の学校コード",
}


# ==========================================
# CSV Helpers
# CSV処理
# ==========================================

def normalize_value(value: str | None) -> str:
    """
    比較時の空値表現を統一する。

    Noneと空文字の差だけで変更扱いにならないようにする。
    """

    if value is None:
        return ""

    return value.strip()


def read_csv_text(text: str) -> dict[str, dict[str, str]]:
    """
    CSVテキストを学校コードをキーとする辞書へ変換する。
    """

    rows: dict[str, dict[str, str]] = {}

    reader = csv.DictReader(text.splitlines())

    if reader.fieldnames is None:
        raise RuntimeError(
            "CSVヘッダーを取得できませんでした。"
        )

    if PRIMARY_KEY not in reader.fieldnames:
        raise RuntimeError(
            f"CSVに必須列 {PRIMARY_KEY} がありません。"
        )

    for row in reader:
        school_code = normalize_value(
            row.get(PRIMARY_KEY)
        )

        if not school_code:
            raise RuntimeError(
                "学校コードが空のレコードを検出しました。"
            )

        if school_code in rows:
            raise RuntimeError(
                f"学校コードが重複しています: {school_code}"
            )

        rows[school_code] = {
            key: normalize_value(value)
            for key, value in row.items()
            if key is not None
        }

    return rows


def read_current_csv() -> dict[str, dict[str, str]]:
    """
    working tree上の現在版schools.csvを読み込む。
    """

    if not CURRENT_CSV_PATH.exists():
        raise FileNotFoundError(
            f"現在版CSVが見つかりません: "
            f"{CURRENT_CSV_PATH}"
        )

    text = CURRENT_CSV_PATH.read_text(
        encoding="utf-8-sig"
    )

    return read_csv_text(text)


# ==========================================
# Git
# Git履歴から前回版を取得
# ==========================================

def read_previous_csv_from_git() -> dict[str, dict[str, str]]:
    """
    Git HEADに保存されている前回版schools.csvを取得する。

    working treeのファイルを上書きしていても、
    HEADにはコミット済みの前回版が残っているため、
    別途previous/ディレクトリを持たずに比較できる。
    """

    command = [
        "git",
        "show",
        f"HEAD:{REPOSITORY_RELATIVE_CSV_PATH}",
    ]

    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        stderr = completed.stderr.decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            "Git HEADから前回版schools.csvを"
            "取得できませんでした。\n"
            f"{stderr}"
        )

    text = completed.stdout.decode(
        "utf-8-sig"
    )

    return read_csv_text(text)


# ==========================================
# Comparison
# 比較処理
# ==========================================

def compare_records(
    previous: dict[str, dict[str, str]],
    current: dict[str, dict[str, str]],
) -> tuple[
    list[str],
    list[str],
    list[dict[str, Any]],
]:
    """
    前回版と現在版を学校コード単位で比較する。

    Returns:
        added_codes
        removed_codes
        changed_records
    """

    previous_codes = set(previous)
    current_codes = set(current)

    added_codes = sorted(
        current_codes - previous_codes
    )

    removed_codes = sorted(
        previous_codes - current_codes
    )

    changed_records: list[
        dict[str, Any]
    ] = []

    common_codes = sorted(
        previous_codes & current_codes
    )

    for school_code in common_codes:
        before = previous[school_code]
        after = current[school_code]

        field_changes: list[
            dict[str, str]
        ] = []

        for field in COMPARISON_FIELDS:
            before_value = before.get(
                field,
                "",
            )

            after_value = after.get(
                field,
                "",
            )

            if before_value == after_value:
                continue

            field_changes.append(
                {
                    "field": field,
                    "before": before_value,
                    "after": after_value,
                }
            )

        if field_changes:
            changed_records.append(
                {
                    "school_code": school_code,
                    "school_name_before":
                        before.get(
                            "school_name",
                            "",
                        ),
                    "school_name_after":
                        after.get(
                            "school_name",
                            "",
                        ),
                    "changes": field_changes,
                }
            )

    return (
        added_codes,
        removed_codes,
        changed_records,
    )


# ==========================================
# Markdown Helpers
# Markdown出力
# ==========================================

def escape_markdown_table(
    value: str,
) -> str:
    """
    Markdown表を壊さないよう最低限エスケープする。
    """

    return (
        value
        .replace("|", r"\|")
        .replace("\n", "<br>")
    )


def display_value(
    value: str,
) -> str:
    """
    空値をMarkdown上で見分けやすく表示する。
    """

    if value == "":
        return "—"

    return escape_markdown_table(
        value
    )


def append_added_section(
    lines: list[str],
    added_codes: list[str],
    current: dict[str, dict[str, str]],
) -> None:
    """
    追加された学校一覧をMarkdownへ追加する。
    """

    lines.append("## 追加")
    lines.append("")

    if not added_codes:
        lines.append("なし")
        lines.append("")
        return

    lines.append(
        "| 学校コード | 学校名 | 都道府県 | 学校種 |"
    )
    lines.append(
        "| --- | --- | --- | --- |"
    )

    for school_code in added_codes:
        row = current[school_code]

        lines.append(
            "| "
            f"`{school_code}` | "
            f"{display_value(row.get('school_name', ''))} | "
            f"{display_value(row.get('prefecture_name', ''))} | "
            f"{display_value(row.get('school_type_name_ja', ''))} |"
        )

    lines.append("")


def append_removed_section(
    lines: list[str],
    removed_codes: list[str],
    previous: dict[str, dict[str, str]],
) -> None:
    """
    前回版から消えた学校一覧をMarkdownへ追加する。

    ここでは「廃止」と断定せず「削除」と表現する。
    一次情報源から消えた理由は別途確認が必要なため。
    """

    lines.append("## 削除")
    lines.append("")

    if not removed_codes:
        lines.append("なし")
        lines.append("")
        return

    lines.append(
        "| 学校コード | 学校名 | 都道府県 | 学校種 |"
    )
    lines.append(
        "| --- | --- | --- | --- |"
    )

    for school_code in removed_codes:
        row = previous[school_code]

        lines.append(
            "| "
            f"`{school_code}` | "
            f"{display_value(row.get('school_name', ''))} | "
            f"{display_value(row.get('prefecture_name', ''))} | "
            f"{display_value(row.get('school_type_name_ja', ''))} |"
        )

    lines.append("")


def append_changed_section(
    lines: list[str],
    changed_records: list[dict[str, Any]],
) -> None:
    """
    変更された学校と変更フィールドをMarkdownへ追加する。
    """

    lines.append("## 変更")
    lines.append("")

    if not changed_records:
        lines.append("なし")
        lines.append("")
        return

    for record in changed_records:
        school_code = record[
            "school_code"
        ]

        school_name = (
            record["school_name_after"]
            or record["school_name_before"]
            or "(名称なし)"
        )

        lines.append(
            f"### {escape_markdown_table(school_name)} "
            f"(`{school_code}`)"
        )
        lines.append("")

        lines.append(
            "| 項目 | 前回 | 今回 |"
        )
        lines.append(
            "| --- | --- | --- |"
        )

        for change in record["changes"]:
            field = change["field"]

            field_label = (
                FIELD_LABELS_JA.get(
                    field,
                    field,
                )
            )

            lines.append(
                "| "
                f"{escape_markdown_table(field_label)} | "
                f"{display_value(change['before'])} | "
                f"{display_value(change['after'])} |"
            )

        lines.append("")


def build_markdown_report(
    previous: dict[str, dict[str, str]],
    current: dict[str, dict[str, str]],
    added_codes: list[str],
    removed_codes: list[str],
    changed_records: list[dict[str, Any]],
) -> str:
    """
    比較結果からMarkdownレポートを生成する。
    """

    lines: list[str] = []

    lines.append(
        "# MEXT School Codes Change Report"
    )
    lines.append("")

    lines.append(
        "GitのHEADに保存された前回版と、"
        "現在生成された `schools.csv` を"
        "学校コード単位で比較した結果です。"
    )
    lines.append("")

    lines.append(
        "> このレポートは機械的な差分検出結果です。"
        "一次情報源における制度上の意味や変更理由を"
        "自動的に判断するものではありません。"
    )
    lines.append("")

    lines.append("## 概要")
    lines.append("")

    lines.append(
        f"- 前回レコード数: "
        f"**{len(previous):,}**"
    )
    lines.append(
        f"- 今回レコード数: "
        f"**{len(current):,}**"
    )
    lines.append(
        f"- 追加: "
        f"**{len(added_codes):,}**"
    )
    lines.append(
        f"- 削除: "
        f"**{len(removed_codes):,}**"
    )
    lines.append(
        f"- 変更: "
        f"**{len(changed_records):,}**"
    )
    lines.append("")

    append_added_section(
        lines,
        added_codes,
        current,
    )

    append_removed_section(
        lines,
        removed_codes,
        previous,
    )

    append_changed_section(
        lines,
        changed_records,
    )

    return "\n".join(lines)


# ==========================================
# Main
# メイン処理
# ==========================================

def main() -> int:
    """
    前回版と現在版を比較し、
    reports/latest-changes.md を生成する。
    """

    print(
        "MEXT School Codes comparator"
    )
    print(
        "----------------------------"
    )

    try:
        print(
            "Reading previous data "
            "from Git HEAD..."
        )

        previous = (
            read_previous_csv_from_git()
        )

        print(
            f"Previous records: "
            f"{len(previous):,}"
        )

        print(
            "Reading current data..."
        )

        current = (
            read_current_csv()
        )

        print(
            f"Current records: "
            f"{len(current):,}"
        )

        (
            added_codes,
            removed_codes,
            changed_records,
        ) = compare_records(
            previous,
            current,
        )

        print()
        print("Comparison result")
        print("-----------------")
        print(
            f"Added:   "
            f"{len(added_codes):,}"
        )
        print(
            f"Removed: "
            f"{len(removed_codes):,}"
        )
        print(
            f"Changed: "
            f"{len(changed_records):,}"
        )

        report = (
            build_markdown_report(
                previous=previous,
                current=current,
                added_codes=added_codes,
                removed_codes=removed_codes,
                changed_records=
                    changed_records,
            )
        )

        REPORTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        REPORT_PATH.write_text(
            report + "\n",
            encoding="utf-8",
            newline="\n",
        )

        print()
        print(
            f"Report written: "
            f"{REPORT_PATH}"
        )

        return 0

    except (
        FileNotFoundError,
        OSError,
        RuntimeError,
        UnicodeError,
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
