#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validate normalized MEXT School Codes data.

文部科学省「学校コード」をもとに生成した二次データについて、
構造、統制語彙、出力形式間の整合性を検証する。

Design principles
-----------------
- metadata.yaml is the source of truth for controlled vocabularies
  and identifier formats.
- Classification values and identifier patterns are not hard-coded
  in this validator.
- Unknown source values are treated as errors, not silently discarded.
- Metadata values absent from the current source are warnings, not errors.
- Secondary data is validated as a fully regenerated dataset.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


# ==========================================
# Paths
# パス
# ==========================================

SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR.parent

METADATA_PATH = DATASET_DIR / "metadata.yaml"
SOURCES_DIR = DATASET_DIR / "sources"
DATA_DIR = DATASET_DIR / "data"

YAML_PATH = DATA_DIR / "schools.yaml"
JSON_PATH = DATA_DIR / "schools.json"
CSV_PATH = DATA_DIR / "schools.csv"


# ==========================================
# Source column names
# 一次情報源の列名
# ==========================================

# 一次CSVの列名は、検証対象となる一次情報源そのものの仕様である。
# 正規化後のフィールド名とは混在させず、ここで明示的に扱う。

SOURCE_COLUMN_SCHOOL_CODE = "学校コード"
SOURCE_COLUMN_SCHOOL_TYPE = "学校種"
SOURCE_COLUMN_PREFECTURE = "都道府県番号"
SOURCE_COLUMN_FOUNDER = "設置\n区分"
SOURCE_COLUMN_SCHOOL_STATUS = "本分校"


# ==========================================
# Validation result collector
# 検証結果
# ==========================================

class ValidationResults:
    """PASS / WARNING / ERROR を集約する。"""

    def __init__(self) -> None:
        self.passes: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def passed(self, message: str) -> None:
        self.passes.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def print_report(self) -> None:
        """GitHub Actionsのログでも読みやすい形式で結果を表示する。"""

        print()
        print("Validation report")
        print("=================")

        for message in self.passes:
            print(f"[PASS]    {message}")

        for message in self.warnings:
            print(f"[WARNING] {message}")

        for message in self.errors:
            print(f"[ERROR]   {message}")

        print()
        print("Summary")
        print("-------")
        print(f"PASS:    {len(self.passes)}")
        print(f"WARNING: {len(self.warnings)}")
        print(f"ERROR:   {len(self.errors)}")


# ==========================================
# Basic loaders
# 基本読み込み処理
# ==========================================

def load_metadata() -> dict[str, Any]:
    """metadata.yaml を読み込む。"""

    with METADATA_PATH.open("r", encoding="utf-8") as file:
        metadata = yaml.safe_load(file)

    if not isinstance(metadata, dict):
        raise ValueError(
            "metadata.yaml のルート要素がmappingではありません。"
        )

    return metadata


def find_source_files() -> list[Path]:
    """sources/ に保存された一次CSVを列挙する。"""

    files = sorted(SOURCES_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError(
            f"一次CSVが見つかりません: {SOURCES_DIR}"
        )

    return files


def read_source_csv(path: Path) -> list[dict[str, str]]:
    """
    文科省CSVを読み込む。

    現行の一次CSVでは第1行がタイトル、
    第2行が列見出しになっている。
    """

    with path.open(
        "r",
        encoding="cp932",
        newline="",
    ) as file:

        # 第1行は「文部科学省 学校コード一覧」等のタイトル行なので、
        # 第2行をDictReaderのヘッダーとして扱う。
        next(file, None)
        reader = csv.DictReader(file)

        return [
            {
                key: value if value is not None else ""
                for key, value in row.items()
                if key is not None
            }
            for row in reader
        ]


def load_all_source_records(
    source_files: list[Path],
) -> list[dict[str, str]]:
    """複数の一次CSVを一つのレコード集合として読み込む。"""

    records: list[dict[str, str]] = []

    for path in source_files:
        file_records = read_source_csv(path)
        records.extend(file_records)

        print(
            f"Reading source: {path.name} "
            f"({len(file_records):,} records)"
        )

    return records


def load_yaml_records() -> list[dict[str, Any]]:
    """生成済み schools.yaml を読み込む。"""

    with YAML_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return extract_records(data, "YAML")


def load_json_records() -> list[dict[str, Any]]:
    """生成済み schools.json を読み込む。"""

    with JSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return extract_records(data, "JSON")


def load_csv_records() -> list[dict[str, str]]:
    """生成済み schools.csv を読み込む。"""

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def extract_records(
    data: Any,
    format_name: str,
) -> list[dict[str, Any]]:
    """
    YAML / JSON のレコード配列を取り出す。

    normalize.py の出力がリストそのものの場合と、
    {"schools": [...]} のようなラッパーを持つ場合の双方を許容する。
    """

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for candidate_key in ("schools", "records", "data"):
            candidate = data.get(candidate_key)

            if isinstance(candidate, list):
                return candidate

    raise ValueError(
        f"{format_name} から学校レコード配列を特定できませんでした。"
    )


# ==========================================
# Metadata helpers
# メタデータ参照
# ==========================================

def get_school_code_pattern(
    metadata: dict[str, Any],
) -> re.Pattern[str]:
    """
    学校コードの形式をmetadata.yamlから取得する。

    学校コード体系の仕様をvalidator側へ重複して記述しないことで、
    metadata.yamlを識別子形式の正本とする。
    """

    pattern_text = (
        metadata
        .get("identifier_format", {})
        .get("school_code", {})
        .get("pattern")
    )

    if not pattern_text:
        raise ValueError(
            "metadata.yaml に "
            "identifier_format.school_code.pattern "
            "が定義されていません。"
        )

    try:
        return re.compile(str(pattern_text))

    except re.error as error:
        raise ValueError(
            "metadata.yaml の "
            "identifier_format.school_code.pattern "
            f"が正しい正規表現ではありません: {error}"
        ) from error


# ==========================================
# Controlled vocabulary helpers
# 統制語彙処理
# ==========================================

def get_metadata_vocabulary(
    metadata: dict[str, Any],
    vocabulary_name: str,
) -> list[dict[str, Any]]:
    """metadata.yaml から指定された統制語彙を取得する。"""

    coverage = metadata.get("coverage", {})
    vocabulary = coverage.get(vocabulary_name)

    if not isinstance(vocabulary, list):
        raise ValueError(
            f"metadata.yaml に coverage.{vocabulary_name} "
            "が定義されていません。"
        )

    return vocabulary


def metadata_codes(
    vocabulary: list[dict[str, Any]],
) -> set[str]:
    """統制語彙からcode集合を取得する。"""

    return {
        str(item["code"]).strip()
        for item in vocabulary
        if item.get("code") is not None
    }


def metadata_source_labels(
    vocabulary: list[dict[str, Any]],
) -> set[str]:
    """
    source_label / source_labels の双方を同じ方法で扱う。

    単数・複数というmetadata上の表現差をvalidator側で吸収することで、
    個別の統制語彙ごとの検証ロジックを作らない。
    """

    labels: set[str] = set()

    for item in vocabulary:
        source_label = item.get("source_label")

        if source_label:
            labels.add(str(source_label).strip())

        source_labels = item.get("source_labels", [])

        if isinstance(source_labels, list):
            labels.update(
                str(label).strip()
                for label in source_labels
                if label is not None
            )

    return labels


def extract_code_from_source_label(value: str) -> str:
    """
    「A1(幼稚園)」「01(北海道)」「1(国)」等からコード部分を取得する。

    意味そのものはmetadata.yamlが管理するため、
    validatorは括弧より前をコードとして分離することだけを担当する。
    """

    value = value.strip()

    if not value:
        return ""

    return value.split("(", 1)[0].strip()


# ==========================================
# Controlled vocabulary validation
# 統制語彙検証
# ==========================================

def validate_vocabulary(
    *,
    results: ValidationResults,
    source_records: list[dict[str, str]],
    metadata: dict[str, Any],
    vocabulary_name: str,
    source_column: str,
    display_name: str,
) -> None:
    """
    一次データとmetadata.yamlの統制語彙を双方向に比較する。

    source ∩ metadata -> PASS
    source - metadata -> ERROR
    metadata - source -> WARNING
    """

    vocabulary = get_metadata_vocabulary(
        metadata,
        vocabulary_name,
    )

    known_codes = metadata_codes(vocabulary)
    known_labels = metadata_source_labels(vocabulary)

    observed_labels = {
        row.get(source_column, "").strip()
        for row in source_records
        if row.get(source_column, "").strip()
    }

    observed_codes = {
        extract_code_from_source_label(label)
        for label in observed_labels
    }

    unknown_codes = observed_codes - known_codes
    unused_codes = known_codes - observed_codes

    unknown_labels = observed_labels - known_labels

    if unknown_codes:
        results.error(
            f"{display_name}: metadata.yaml に未定義のコードを検出: "
            f"{', '.join(sorted(unknown_codes))}"
        )
    else:
        results.passed(
            f"{display_name}: 一次データの全コードがmetadata.yamlに定義済み "
            f"({len(observed_codes)} values)"
        )

    # コード自体が既知でも一次情報源側のラベルが変更されていれば、
    # metadata.yamlの再確認が必要なので検出する。
    if unknown_labels:
        results.error(
            f"{display_name}: metadata.yaml に未定義のsource_labelを検出: "
            f"{', '.join(sorted(unknown_labels))}"
        )
    else:
        results.passed(
            f"{display_name}: 一次データのsource_labelがmetadata.yamlと一致"
        )

    # metadata側にのみ存在する値は制度上有効だが該当データが0件という
    # 可能性があるため、自動削除せずWARNINGとして人間の確認対象にする。
    if unused_codes:
        results.warning(
            f"{display_name}: metadata.yamlには存在するが "
            f"今回の一次データには現れないコード: "
            f"{', '.join(sorted(unused_codes))}"
        )


# ==========================================
# Structural validation
# 構造検証
# ==========================================

POSTAL_CODE_PATTERN = re.compile(r"^[0-9]{7}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_school_codes(
    results: ValidationResults,
    source_records: list[dict[str, str]],
    school_code_pattern: re.Pattern[str],
) -> None:
    """
    学校コードの欠損、形式、重複を検証する。

    形式そのものはmetadata.yamlから渡されるため、
    この関数は学校コードが何桁なのかを知らない。
    """

    school_codes = [
        row.get(SOURCE_COLUMN_SCHOOL_CODE, "").strip()
        for row in source_records
    ]

    missing_count = sum(
        1
        for code in school_codes
        if not code
    )

    if missing_count:
        results.error(
            f"学校コード: 空欄レコード {missing_count:,} 件"
        )
    else:
        results.passed(
            "学校コード: 欠損なし"
        )

    invalid_codes = sorted({
        code
        for code in school_codes
        if code
        and not school_code_pattern.fullmatch(code)
    })

    if invalid_codes:
        preview = ", ".join(
            invalid_codes[:10]
        )

        results.error(
            f"学校コード: 形式不正 "
            f"{len(invalid_codes):,} values "
            f"(examples: {preview})"
        )
    else:
        results.passed(
            "学校コード: "
            "metadata.yamlの識別子形式に適合"
        )

    counts = Counter(
        code
        for code in school_codes
        if code
    )

    duplicates = sorted(
        code
        for code, count in counts.items()
        if count > 1
    )

    if duplicates:
        preview = ", ".join(
            duplicates[:10]
        )

        results.error(
            f"学校コード: 重複 "
            f"{len(duplicates):,} values "
            f"(examples: {preview})"
        )
    else:
        results.passed(
            "学校コード: 重複なし"
        )


def validate_date_value(value: str) -> bool:
    """日付が実在するYYYY-MM-DDであることを確認する。"""

    value = value.strip()

    if not value:
        return True

    if not DATE_PATTERN.fullmatch(value):
        return False

    try:
        datetime.strptime(
            value,
            "%Y-%m-%d",
        )

    except ValueError:
        return False

    return True


# ==========================================
# Cross-format validation
# 出力形式間検証
# ==========================================

def find_school_code_field(
    record: dict[str, Any],
) -> str | None:
    """
    正規化データから学校コードを取得する。

    normalize.pyの現在の出力構造との接続点を
    この関数一箇所に集約する。
    """

    for candidate in (
        "school_code",
        "code",
    ):
        value = record.get(candidate)

        if value is not None:
            return str(value).strip()

    return None


def get_school_code_set(
    records: list[dict[str, Any]],
    format_name: str,
    results: ValidationResults,
) -> set[str]:
    """正規化出力から学校コード集合を作る。"""

    codes: set[str] = set()
    missing = 0

    for record in records:
        code = find_school_code_field(
            record
        )

        if code:
            codes.add(code)
        else:
            missing += 1

    if missing:
        results.error(
            f"{format_name}: "
            f"school_codeを取得できないレコード "
            f"{missing:,} 件"
        )

    return codes


def validate_record_counts(
    results: ValidationResults,
    *,
    source_records: list[dict[str, str]],
    yaml_records: list[dict[str, Any]],
    json_records: list[dict[str, Any]],
    csv_records: list[dict[str, str]],
) -> None:
    """一次データと全配布形式のレコード件数を比較する。"""

    counts = {
        "source": len(source_records),
        "YAML": len(yaml_records),
        "JSON": len(json_records),
        "CSV": len(csv_records),
    }

    if len(set(counts.values())) == 1:
        count = next(
            iter(counts.values())
        )

        results.passed(
            f"レコード件数: "
            f"全形式一致 ({count:,} records)"
        )

    else:
        results.error(
            "レコード件数が一致しません: "
            + ", ".join(
                f"{name}={count:,}"
                for name, count
                in counts.items()
            )
        )


def validate_school_code_sets(
    results: ValidationResults,
    *,
    source_records: list[dict[str, str]],
    yaml_records: list[dict[str, Any]],
    json_records: list[dict[str, Any]],
    csv_records: list[dict[str, str]],
) -> None:
    """全形式に同じ学校コード集合が含まれていることを確認する。"""

    source_codes = {
        row.get(
            SOURCE_COLUMN_SCHOOL_CODE,
            "",
        ).strip()
        for row in source_records
        if row.get(
            SOURCE_COLUMN_SCHOOL_CODE,
            "",
        ).strip()
    }

    yaml_codes = get_school_code_set(
        yaml_records,
        "YAML",
        results,
    )

    json_codes = get_school_code_set(
        json_records,
        "JSON",
        results,
    )

    csv_codes = get_school_code_set(
        csv_records,
        "CSV",
        results,
    )

    code_sets = {
        "source": source_codes,
        "YAML": yaml_codes,
        "JSON": json_codes,
        "CSV": csv_codes,
    }

    reference = source_codes
    mismatches: list[str] = []

    for name, codes in code_sets.items():

        if codes != reference:
            missing = reference - codes
            extra = codes - reference

            mismatches.append(
                f"{name}: "
                f"missing={len(missing):,}, "
                f"extra={len(extra):,}"
            )

    if mismatches:
        results.error(
            "学校コード集合が一致しません: "
            + "; ".join(mismatches)
        )

    else:
        results.passed(
            f"学校コード集合: 全形式一致 "
            f"({len(reference):,} unique codes)"
        )


# ==========================================
# Required files
# 必須ファイル検証
# ==========================================

def validate_required_files(
    results: ValidationResults,
) -> bool:
    """検証に必要なファイルが揃っているか確認する。"""

    required_paths = [
        METADATA_PATH,
        YAML_PATH,
        JSON_PATH,
        CSV_PATH,
    ]

    missing = [
        path
        for path in required_paths
        if not path.exists()
    ]

    if missing:
        for path in missing:
            results.error(
                f"必須ファイルがありません: {path}"
            )

        return False

    results.passed(
        "検証対象ファイル: 必須ファイル確認済み"
    )

    return True


# ==========================================
# Main validation workflow
# 検証ワークフロー
# ==========================================

def main() -> int:

    print(
        "MEXT School Codes validator"
    )
    print(
        "---------------------------"
    )

    results = ValidationResults()

    try:

        if not validate_required_files(
            results
        ):
            results.print_report()
            return 1

        # ------------------------------------------
        # Metadata
        # メタデータ
        # ------------------------------------------

        metadata = load_metadata()

        school_code_pattern = (
            get_school_code_pattern(
                metadata
            )
        )

        # ------------------------------------------
        # Primary source
        # 一次データ
        # ------------------------------------------

        source_files = find_source_files()

        print(
            f"Source files: "
            f"{len(source_files)}"
        )

        source_records = (
            load_all_source_records(
                source_files
            )
        )

        print()
        print(
            f"Total source records: "
            f"{len(source_records):,}"
        )

        # ------------------------------------------
        # Structural validation
        # 構造検証
        # ------------------------------------------

        validate_school_codes(
            results,
            source_records,
            school_code_pattern,
        )

        # ------------------------------------------
        # Controlled vocabulary validation
        # 統制語彙検証
        # ------------------------------------------

        validate_vocabulary(
            results=results,
            source_records=source_records,
            metadata=metadata,
            vocabulary_name="institution_types",
            source_column=SOURCE_COLUMN_SCHOOL_TYPE,
            display_name="学校種",
        )

        validate_vocabulary(
            results=results,
            source_records=source_records,
            metadata=metadata,
            vocabulary_name="prefectures",
            source_column=SOURCE_COLUMN_PREFECTURE,
            display_name="都道府県",
        )

        validate_vocabulary(
            results=results,
            source_records=source_records,
            metadata=metadata,
            vocabulary_name="founder_types",
            source_column=SOURCE_COLUMN_FOUNDER,
            display_name="設置区分",
        )

        validate_vocabulary(
            results=results,
            source_records=source_records,
            metadata=metadata,
            vocabulary_name="school_status",
            source_column=SOURCE_COLUMN_SCHOOL_STATUS,
            display_name="本分校区分",
        )

        # ------------------------------------------
        # Generated secondary data
        # 生成済み二次データ
        # ------------------------------------------

        print()
        print(
            "Reading generated data..."
        )

        yaml_records = (
            load_yaml_records()
        )

        print(
            f"YAML: "
            f"{len(yaml_records):,} records"
        )

        json_records = (
            load_json_records()
        )

        print(
            f"JSON: "
            f"{len(json_records):,} records"
        )

        csv_records = (
            load_csv_records()
        )

        print(
            f"CSV:  "
            f"{len(csv_records):,} records"
        )

        # ------------------------------------------
        # Cross-format validation
        # 出力形式間検証
        # ------------------------------------------

        validate_record_counts(
            results,
            source_records=source_records,
            yaml_records=yaml_records,
            json_records=json_records,
            csv_records=csv_records,
        )

        validate_school_code_sets(
            results,
            source_records=source_records,
            yaml_records=yaml_records,
            json_records=json_records,
            csv_records=csv_records,
        )

    except Exception as error:
        results.error(
            f"Validator execution error: "
            f"{error}"
        )

    # ------------------------------------------
    # Report
    # 結果表示
    # ------------------------------------------

    results.print_report()

    if results.has_errors:
        print()
        print(
            "Validation FAILED."
        )

        return 1

    print()
    print(
        "Validation PASSED."
    )

    if results.warnings:
        print(
            "Warnings were detected, "
            "but they do not prevent publication."
        )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )