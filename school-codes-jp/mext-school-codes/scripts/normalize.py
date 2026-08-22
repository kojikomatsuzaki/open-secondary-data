#!/usr/bin/env python3

"""
文部科学省「学校コード」CSVを正規化し、
YAML / JSON / CSV の二次データを生成する。

一次情報源:
https://www.mext.go.jp/b_menu/toukei/mext_01087.html

このスクリプトでは、コード体系や正規化名称をコード内に重複定義せず、
dataset root の metadata.yaml を正本として参照する。

Input:
    sources/*.csv
    metadata.yaml

Output:
    data/schools.yaml
    data/schools.json
    data/schools.csv
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


# ==========================================
# Paths
# ==========================================

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
DATASET_DIRECTORY = SCRIPT_DIRECTORY.parent

METADATA_FILE = DATASET_DIRECTORY / "metadata.yaml"
SOURCES_DIRECTORY = DATASET_DIRECTORY / "sources"
DATA_DIRECTORY = DATASET_DIRECTORY / "data"

YAML_OUTPUT_FILE = DATA_DIRECTORY / "schools.yaml"
JSON_OUTPUT_FILE = DATA_DIRECTORY / "schools.json"
CSV_OUTPUT_FILE = DATA_DIRECTORY / "schools.csv"


# ==========================================
# Source Column Names
# ==========================================

# 列名そのものをここで「意味変換」するのではなく、
# 文科省CSVの物理的な列名と内部フィールドとの対応だけを定義する。
#
# 学校種や設置区分などの意味上の定義は metadata.yaml を正本とする。

SOURCE_COLUMN_MAP = {
    "学校コード": "school_code",
    "学校種": "school_type",
    "都道府県番号": "prefecture",
    "設置区分": "founder",
    "本分校": "school_status",
    "学校名": "school_name",
    "学校所在地": "address",
    "郵便番号": "postal_code",
    "属性情報設定年月日": "attribute_set_date",
    "属性情報廃止年月日": "attribute_abolished_date",
    "旧学校調査番号": "obsolete_school_survey_number",
    "移行後の学校コード": "successor_school_code",
}


# ==========================================
# Metadata
# ==========================================

def load_metadata() -> dict[str, Any]:
    """
    metadata.yaml を読み込む。

    コード体系の意味をPython側へ重複して持たせないため、
    metadata.yaml を正規化ルールの正本として利用する。
    """

    if not METADATA_FILE.exists():
        raise RuntimeError(
            f"metadata.yaml が見つかりません: {METADATA_FILE}"
        )

    with METADATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata = yaml.safe_load(file)

    if not isinstance(metadata, dict):
        raise RuntimeError(
            "metadata.yaml のルートが辞書形式ではありません。"
        )

    return metadata


def build_normalization_lookup(
    items: list[dict[str, Any]],
    multiple_source_labels: bool = False,
) -> dict[str, dict[str, Any]]:
    """
    metadata.yaml のコード定義を検索しやすい辞書へ変換する。

    例:
        "A1" -> {
            "ja": "幼稚園",
            "en": "Kindergarten",
            ...
        }

    E1のように複数のsource_labelsを持つケースも許容する。
    """

    lookup: dict[str, dict[str, Any]] = {}

    for item in items:
        code = str(item["code"])

        if multiple_source_labels:
            source_labels = item.get(
                "source_labels",
                [],
            )
        else:
            source_label = item.get(
                "source_label"
            )
            source_labels = (
                [source_label]
                if source_label
                else []
            )

        lookup[code] = {
            "source_labels": source_labels,
            "normalized_name": item.get(
                "normalized_name",
                {},
            ),
        }

    return lookup


# ==========================================
# Source Format
# ==========================================

def normalize_column_name(
    column_name: str,
) -> str:
    """
    CSVヘッダー内の改行や余分な空白を除去する。

    文科省CSVには
    「設置\\n区分」
    「属性情報\\n設定年月日」
    のようなセル内改行が存在する。

    表示上の都合による改行は項目の意味ではないため、
    正規化時に除去する。
    """

    return re.sub(
        r"\s+",
        "",
        column_name,
    )


def clean_value(
    value: str | None,
) -> str | None:
    """
    空文字をNoneへ統一する。

    コードや郵便番号などは先頭ゼロを保持する必要があるため、
    数値型へ変換せず、文字列のまま扱う。
    """

    if value is None:
        return None

    cleaned = value.strip()

    if cleaned == "":
        return None

    return cleaned


# ==========================================
# Compound Values
# ==========================================

COMPOUND_VALUE_PATTERN = re.compile(
    r"^(?P<code>[^()]+)\((?P<label>.*)\)$"
)


def split_compound_value(
    value: str | None,
) -> tuple[str | None, str | None]:
    """
    「A1(幼稚園)」「01(北海道)」「2(公)」のような値を、
    コードと表示名に分離する。

    元の値そのものは別途source_labelとして保持するため、
    一次情報源の表記を失わない。
    """

    if value is None:
        return None, None

    match = COMPOUND_VALUE_PATTERN.match(
        value
    )

    if match is None:
        return value, None

    return (
        match.group("code"),
        match.group("label"),
    )


def normalize_coded_value(
    source_value: str | None,
    lookup: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """
    metadata.yaml を使ってコード値を正規化する。

    source_labelには原CSVの値をそのまま保持することで、
    元資料との照合可能性を維持する。
    """

    if source_value is None:
        return None

    code, source_name = split_compound_value(
        source_value
    )

    result: dict[str, Any] = {
        "code": code,
        "source_label": source_value,
    }

    if source_name is not None:
        result["source_name"] = source_name

    metadata_definition = lookup.get(
        code or ""
    )

    if metadata_definition:
        normalized_name = (
            metadata_definition.get(
                "normalized_name"
            )
        )

        if normalized_name:
            result["normalized_name"] = (
                normalized_name
            )

    return result


def normalize_prefecture(
    source_value: str | None,
) -> dict[str, Any] | None:
    """
    都道府県番号をコードと名称へ分離する。

    都道府県名称の独立した正本は本データセットでは持たず、
    文科省CSVに記載された名称を保持する。

    将来、都道府県マスターデータを別データセットとして
    整備した場合は、その識別子との接続を検討できる。
    """

    if source_value is None:
        return None

    code, source_name = split_compound_value(
        source_value
    )

    return {
        "code": code,
        "source_label": source_value,
        "name": source_name,
    }


# ==========================================
# CSV Reader
# ==========================================

def read_source_csv(
    source_file: Path,
    encoding: str,
) -> list[dict[str, str | None]]:
    """
    文科省CSVを読み込む。

    1行目はタイトル・更新日であり、
    2行目が実際のヘッダーであるため、
    先頭行を明示的に読み飛ばす。
    """

    rows: list[
        dict[str, str | None]
    ] = []

    with source_file.open(
        "r",
        encoding=encoding,
        newline="",
    ) as file:

        # 1行目は
        # 「文部科学省 学校コード一覧 / 更新日」
        # なのでデータヘッダーとして使用しない。
        next(file, None)

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise RuntimeError(
                f"CSVヘッダーを取得できません: "
                f"{source_file}"
            )

        normalized_fieldnames = [
            normalize_column_name(name)
            for name in reader.fieldnames
        ]

        expected_columns = set(
            SOURCE_COLUMN_MAP.keys()
        )

        actual_columns = set(
            normalized_fieldnames
        )

        missing_columns = (
            expected_columns
            - actual_columns
        )

        if missing_columns:
            raise RuntimeError(
                "CSVに必要な列がありません。\n"
                f"File: {source_file}\n"
                f"Missing: "
                f"{sorted(missing_columns)}"
            )

        for raw_row in reader:
            normalized_row: dict[
                str,
                str | None
            ] = {}

            for original_column_name, value \
                    in raw_row.items():

                if original_column_name is None:
                    continue

                normalized_column_name = (
                    normalize_column_name(
                        original_column_name
                    )
                )

                internal_name = (
                    SOURCE_COLUMN_MAP.get(
                        normalized_column_name
                    )
                )

                if internal_name is None:
                    continue

                normalized_row[
                    internal_name
                ] = clean_value(value)

            rows.append(normalized_row)

    return rows


# ==========================================
# Record Normalization
# ==========================================

def normalize_record(
    row: dict[str, str | None],
    source_file: Path,
    school_type_lookup: dict[
        str,
        dict[str, Any]
    ],
    founder_lookup: dict[
        str,
        dict[str, Any]
    ],
    school_status_lookup: dict[
        str,
        dict[str, Any]
    ],
) -> dict[str, Any]:
    """
    1校分のCSVレコードを二次データ構造へ変換する。
    """

    return {
        "school_code": row.get(
            "school_code"
        ),
        "school_name": row.get(
            "school_name"
        ),

        "school_type":
            normalize_coded_value(
                row.get("school_type"),
                school_type_lookup,
            ),

        "prefecture":
            normalize_prefecture(
                row.get("prefecture")
            ),

        "founder":
            normalize_coded_value(
                row.get("founder"),
                founder_lookup,
            ),

        "school_status":
            normalize_coded_value(
                row.get(
                    "school_status"
                ),
                school_status_lookup,
            ),

        "address": row.get(
            "address"
        ),

        "postal_code": row.get(
            "postal_code"
        ),

        "attribute_set_date":
            row.get(
                "attribute_set_date"
            ),

        "attribute_abolished_date":
            row.get(
                "attribute_abolished_date"
            ),

        "obsolete_school_survey_number":
            row.get(
                "obsolete_school_survey_number"
            ),

        "successor_school_code":
            row.get(
                "successor_school_code"
            ),

        "provenance": {
            "source_file":
                source_file.name,
        },
    }


# ==========================================
# Validation
# ==========================================

def validate_records(
    records: list[dict[str, Any]],
) -> None:
    """
    二次データ生成前に最低限の整合性を確認する。

    学校コードは一意識別子として利用するため、
    重複があれば黙って出力せず処理を停止する。
    """

    school_codes: set[str] = set()

    duplicate_codes: set[str] = set()

    for record in records:
        school_code = record.get(
            "school_code"
        )

        if not school_code:
            raise RuntimeError(
                "学校コードが空の"
                "レコードを検出しました。"
            )

        if school_code in school_codes:
            duplicate_codes.add(
                school_code
            )

        school_codes.add(
            school_code
        )

    if duplicate_codes:
        raise RuntimeError(
            "重複する学校コードを"
            "検出しました:\n"
            + "\n".join(
                sorted(
                    duplicate_codes
                )
            )
        )


# ==========================================
# Output Structure
# ==========================================

def build_output_document(
    records: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    YAML / JSON共通のトップレベル構造を作る。

    実行日時を自動挿入すると、
    データそのものが変わっていなくても毎回diffが発生する。

    そのため、出力には再現性のある
    リリース情報だけを含める。
    """

    current_release = metadata.get(
        "current_release",
        {},
    )

    return {
        "dataset": {
            "id": metadata.get(
                "dataset",
                {},
            ).get(
                "id",
                "mext-school-codes",
            ),
            "reference_date":
                current_release.get(
                    "reference_date"
                ),
            "source_updated_at":
                current_release.get(
                    "source_updated_at"
                ),
            "published_at":
                current_release.get(
                    "published_at"
                ),
            "record_count":
                len(records),
        },
        "schools": records,
    }


# ==========================================
# YAML / JSON Output
# ==========================================

def write_yaml(
    document: dict[str, Any],
) -> None:
    """
    人間にも読みやすい正本用YAMLを出力する。
    """

    with YAML_OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        yaml.safe_dump(
            document,
            file,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=120,
        )


def write_json(
    document: dict[str, Any],
) -> None:
    """
    Web/API等から利用しやすいJSONを出力する。
    """

    with JSON_OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            document,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write("\n")


# ==========================================
# CSV Output
# ==========================================

CSV_COLUMNS = [
    "school_code",
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
    "source_file",
]


def flatten_record_for_csv(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    階層構造を持つYAML/JSONレコードを、
    表形式で利用しやすいCSVへ変換する。
    """

    school_type = (
        record.get("school_type")
        or {}
    )

    prefecture = (
        record.get("prefecture")
        or {}
    )

    founder = (
        record.get("founder")
        or {}
    )

    school_status = (
        record.get("school_status")
        or {}
    )

    provenance = (
        record.get("provenance")
        or {}
    )

    return {
        "school_code":
            record.get("school_code"),

        "school_name":
            record.get("school_name"),

        "school_type_code":
            school_type.get("code"),

        "school_type_source_label":
            school_type.get(
                "source_label"
            ),

        "school_type_name_ja":
            (
                school_type.get(
                    "normalized_name"
                )
                or {}
            ).get("ja"),

        "school_type_name_en":
            (
                school_type.get(
                    "normalized_name"
                )
                or {}
            ).get("en"),

        "prefecture_code":
            prefecture.get("code"),

        "prefecture_name":
            prefecture.get("name"),

        "founder_code":
            founder.get("code"),

        "founder_source_label":
            founder.get(
                "source_label"
            ),

        "founder_name_ja":
            (
                founder.get(
                    "normalized_name"
                )
                or {}
            ).get("ja"),

        "founder_name_en":
            (
                founder.get(
                    "normalized_name"
                )
                or {}
            ).get("en"),

        "school_status_code":
            school_status.get(
                "code"
            ),

        "school_status_source_label":
            school_status.get(
                "source_label"
            ),

        "school_status_name_ja":
            (
                school_status.get(
                    "normalized_name"
                )
                or {}
            ).get("ja"),

        "school_status_name_en":
            (
                school_status.get(
                    "normalized_name"
                )
                or {}
            ).get("en"),

        "address":
            record.get("address"),

        "postal_code":
            record.get("postal_code"),

        "attribute_set_date":
            record.get(
                "attribute_set_date"
            ),

        "attribute_abolished_date":
            record.get(
                "attribute_abolished_date"
            ),

        "obsolete_school_survey_number":
            record.get(
                "obsolete_school_survey_number"
            ),

        "successor_school_code":
            record.get(
                "successor_school_code"
            ),

        "source_file":
            provenance.get(
                "source_file"
            ),
    }


def write_csv(
    records: list[dict[str, Any]],
) -> None:
    """
    表計算ソフト等で再利用しやすいCSVを出力する。

    UTF-8 BOM付きとすることで、
    Windows版Excelで直接開いた場合の
    日本語文字化けを避ける。
    """

    with CSV_OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS,
        )

        writer.writeheader()

        for record in records:
            writer.writerow(
                flatten_record_for_csv(
                    record
                )
            )


# ==========================================
# Main
# ==========================================

def main() -> int:
    """
    sources/ のCSVを統合・正規化し、
    data/ に3形式で出力する。
    """

    print(
        "MEXT School Codes normalizer"
    )
    print(
        "----------------------------"
    )

    try:
        metadata = load_metadata()

        source_encoding = (
            metadata
            .get("source_format", {})
            .get("encoding", "cp932")
        )

        coverage = metadata.get(
            "coverage",
            {},
        )

        school_type_lookup = (
            build_normalization_lookup(
                coverage.get(
                    "institution_types",
                    [],
                ),
                multiple_source_labels=True,
            )
        )

        founder_lookup = (
            build_normalization_lookup(
                coverage.get(
                    "founder_types",
                    [],
                )
            )
        )

        school_status_lookup = (
            build_normalization_lookup(
                coverage.get(
                    "school_status",
                    [],
                )
            )
        )

        source_files = sorted(
            SOURCES_DIRECTORY.glob(
                "*.csv"
            )
        )

        if not source_files:
            raise RuntimeError(
                "sources/ にCSVが"
                "見つかりません。"
            )

        print(
            f"Source files: "
            f"{len(source_files)}"
        )

        records: list[
            dict[str, Any]
        ] = []

        for source_file in source_files:
            print(
                f"Reading: "
                f"{source_file.name}"
            )

            source_rows = (
                read_source_csv(
                    source_file,
                    encoding=source_encoding,
                )
            )

            print(
                f"  Records: "
                f"{len(source_rows)}"
            )

            for row in source_rows:
                records.append(
                    normalize_record(
                        row=row,
                        source_file=source_file,
                        school_type_lookup=
                            school_type_lookup,
                        founder_lookup=
                            founder_lookup,
                        school_status_lookup=
                            school_status_lookup,
                    )
                )

        # 出力順を固定することで、
        # ソースファイルの列挙順が変わっても
        # 不要なGit diffが発生しないようにする。
        records.sort(
            key=lambda record:
                record["school_code"]
        )

        validate_records(records)

        DATA_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        document = (
            build_output_document(
                records,
                metadata,
            )
        )

        write_yaml(document)
        write_json(document)
        write_csv(records)

        print()
        print(
            f"Total records: "
            f"{len(records)}"
        )

        print()
        print("Generated:")
        print(
            f"- {YAML_OUTPUT_FILE}"
        )
        print(
            f"- {JSON_OUTPUT_FILE}"
        )
        print(
            f"- {CSV_OUTPUT_FILE}"
        )

        return 0

    except (
        RuntimeError,
        OSError,
        yaml.YAMLError,
    ) as error:

        print(
            f"Error: {error}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
