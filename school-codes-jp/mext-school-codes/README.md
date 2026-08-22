# MEXT School Codes

文部科学省が公開する「学校コード」を一次情報源として、再利用しやすい形式に整理・構造化した二次データを提供します。

[English follows Japanese.](#english)

---

## 日本語

## 概要

文部科学省では、全国の学校を一意に識別するため、それぞれの学校に唯一の「学校コード」を設定しています。

文部科学省によれば、一度設定された学校コードは変更せず、他の学校には流用しないことを基本としており、学校基本調査をはじめとする統計調査や各種調査研究等で広く活用されることが想定されています。

本データセットでは、文部科学省が公開する「学校コード」を一次情報源とし、データの出典と来歴を明示したうえで、再利用しやすい形式へ整理・構造化した二次データを提供します。

本データセットは文部科学省が提供する公式データそのものではなく、`open-secondary-data` プロジェクトによって作成・管理される二次データです。

---

## 一次情報源

### 文部科学省「学校コード」

* 提供者：文部科学省
* 資料名：文部科学省「学校コード」
* 公式ページ：https://www.mext.go.jp/b_menu/toukei/mext_01087.html
* 最新版：令和8年5月1日時点（暫定版）
* 公表日：令和8年5月29日（2026年5月29日）

公式ページでは、最新版に加えて過去の学校コード一覧、学校コードの取り扱い、都道府県が定める付番方針等も公開されています。

一次情報源の内容は更新される可能性があります。利用時には必要に応じて文部科学省の公式ページも確認してください。

---

## 収録対象

文部科学省が公開する学校コード一覧を対象とします。

現在の学校コード一覧には、次の学校種等が含まれています。

* 幼稚園
* 幼保連携型認定こども園
* 小学校
* 中学校
* 義務教育学校
* 高等学校
* 中等教育学校
* 特別支援学校
* 専修学校
* 各種学校
* 大学
* 短期大学
* 高等専門学校

文部科学省が公開する一次データの構成変更等に伴い、収録対象を変更する場合があります。

---

## データ作成方針

本データセットでは、文部科学省が公開するデータを一次情報源として取得し、再利用しやすい形式へ整理・構造化します。

処理にあたっては、次の原則を採用します。

1. 一次情報源を保存し、取得元と取得日を記録する
2. 一次情報と加工後の二次データを明確に区別する
3. 加工・変換内容を記録する
4. 可能な限り処理をスクリプト化し、再現可能にする
5. 更新時には既存データとの差分を確認する
6. 意味上の判断を伴う変更については人間による確認を行う

具体的なデータ構造および変換方法については、データおよび処理スクリプトの整備にあわせて記録します。

---

## ディレクトリ構成

```text
mext-school-codes/
├── README.md
├── metadata.yaml
├── data/
├── sources/
├── scripts/
└── reports/
```

| ディレクトリ / ファイル   | 役割                             |
| --------------- | ------------------------------ |
| `README.md`     | 本データセットの説明                     |
| `metadata.yaml` | 出典、版、取得日、利用条件、加工内容等の機械可読なメタデータ |
| `data/`         | 整理・構造化した二次データ                  |
| `sources/`      | 文部科学省から取得した一次情報源               |
| `scripts/`      | データの取得、変換、正規化、検証等に使用するスクリプト    |
| `reports/`      | 更新時の差分、検証結果等に関するレポート           |

必要性が生じた場合は、この構造を拡張することがあります。その場合は、追加した階層またはディレクトリの目的をREADME等に記録します。

---

## 更新方針

文部科学省による学校コード一覧の更新を確認し、新しい版が公開された場合は一次情報源を取得します。

更新時には、原則として次の処理を行います。

1. 一次情報源の取得
2. 取得した版および取得日の記録
3. 前版との差分確認
4. 二次データの生成
5. データの検証
6. 必要に応じた人間による確認
7. 更新内容の記録

将来的には、一次情報源の更新確認、取得、差分検出等について、GitHub Actions等による自動化を検討します。

---

## 利用条件

一次情報源である文部科学省ウェブサイトのコンテンツの利用については、文部科学省ウェブサイト利用規約を確認してください。

https://www.mext.go.jp/b_menu/1351168.htm

文部科学省ウェブサイト利用規約では、出典を記載すること、編集・加工等を行った場合はその旨を記載すること等が定められています。

同利用規約は「公共データ利用規約（第1.0版）」に準拠しており、クリエイティブ・コモンズ・ライセンス「表示4.0国際（CC BY 4.0）」と互換性があるとされています。

本データセットでは、一次情報源を明示するとともに、文部科学省が公開するデータを加工して作成した二次データであることを明示します。

なお、一次情報源の利用条件が変更された場合は、最新の利用条件を確認してください。

---

## 注意事項

文部科学省は、学校コード一覧に記載された学校名称、住所、郵便番号について、変更や誤り等がある可能性があり、随時更新するとしています。

本データセットについても、一次情報源の内容および本プロジェクトによる加工処理の双方に起因する誤りが存在する可能性があります。

正確性が重要となる用途では、必ず一次情報源を確認してください。

---

## 管理・プロジェクト情報

このデータセットは `open-secondary-data` プロジェクトの一部として管理されています。

プロジェクトの管理者、問い合わせ先、リポジトリ全体の利用条件に関する基本方針および設計原則については、[ルートREADME](../../README.md) を参照してください。

---

# English

This dataset provides reusable secondary data derived from the official 「学校コード」 (School Codes) published by Japan's Ministry of Education, Culture, Sports, Science and Technology (MEXT).

## Overview

MEXT assigns a unique 「学校コード」 (School Code) to schools throughout Japan in order to provide a publicly available means of uniquely identifying educational institutions.

According to MEXT, once assigned, a School Code is generally not changed or reused for another school. The codes are intended for broad use in statistical surveys, including the School Basic Survey, as well as in research and other forms of data analysis.

This dataset uses the School Codes published by MEXT as its primary source and provides organized and structured secondary data while preserving information about source provenance.

This dataset is not an official MEXT dataset. It is secondary data created and maintained by the `open-secondary-data` project.

---

## Primary Source

### MEXT 「学校コード」

* Publisher: Ministry of Education, Culture, Sports, Science and Technology (MEXT), Japan
* Source title: 「文部科学省　学校コード」
* Official page: https://www.mext.go.jp/b_menu/toukei/mext_01087.html
* Latest version: May 1, 2026 (provisional)
* Publication date: May 29, 2026

The official page also provides previous versions of the School Code lists, documentation concerning the handling of School Codes, and numbering policies established by prefectural authorities.

Because the primary source may be updated, users should consult the official MEXT page when necessary.

---

## Scope

This dataset covers the School Code lists published by MEXT.

The current source includes the following types of institutions:

* Kindergartens
* Integrated Centers for Early Childhood Education and Care
* Elementary Schools
* Junior High Schools
* Compulsory Education Schools
* High Schools
* Secondary Education Schools
* Special Needs Education Schools
* Specialized Training Colleges
* Miscellaneous Schools
* Universities
* Junior Colleges
* Colleges of Technology

The scope may change if MEXT changes the structure or coverage of the primary data.

---

## Data Processing Policy

Data published by MEXT is obtained as the primary source and organized into reusable secondary-data formats.

The following principles are applied:

1. Preserve primary-source data and record its origin and retrieval date
2. Clearly distinguish primary-source material from processed secondary data
3. Document transformations and modifications
4. Automate reproducible processes through scripts whenever practical
5. Compare updates with previous versions
6. Apply human review when changes require semantic judgment

Detailed data structures and transformation procedures will be documented as the dataset and processing scripts are developed.

---

## Directory Structure

```text
mext-school-codes/
├── README.md
├── metadata.yaml
├── data/
├── sources/
├── scripts/
└── reports/
```

| Directory / File | Purpose                                                                                                    |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| `README.md`      | Documentation for this dataset                                                                             |
| `metadata.yaml`  | Machine-readable metadata including provenance, version, retrieval date, terms of use, and transformations |
| `data/`          | Organized and structured secondary data                                                                    |
| `sources/`       | Primary-source files obtained from MEXT                                                                    |
| `scripts/`       | Scripts used for retrieval, conversion, normalization, validation, and related processing                  |
| `reports/`       | Reports concerning differences between versions, validation results, and updates                           |

This structure may be extended when necessary. When additional levels or directories are introduced, their purpose should be documented in the relevant README or other documentation.

---

## Update Policy

When a new version of the School Code list is published by MEXT, the corresponding primary-source data will be obtained.

Updates will generally involve:

1. Retrieving the primary source
2. Recording the version and retrieval date
3. Comparing it with the previous version
4. Generating secondary data
5. Validating the resulting data
6. Applying human review where necessary
7. Recording the update

Future automation using GitHub Actions or similar tools may be introduced for source monitoring, retrieval, and change detection.

---

## Terms of Use

Use of content obtained from the MEXT website is subject to the MEXT Website Terms of Use:

https://www.mext.go.jp/b_menu/1351168.htm

The MEXT Website Terms of Use require appropriate source attribution and, where content has been edited or otherwise modified, disclosure that such modification has been performed.

The terms conform to Japan's Public Data License (Version 1.0) and are compatible with the Creative Commons Attribution 4.0 International License (CC BY 4.0).

This dataset identifies its primary source and explicitly indicates that the secondary data has been created by processing data published by MEXT.

Users should consult the current terms of use if the conditions governing the primary source change.

---

## Notes

MEXT notes that school names, addresses, and postal codes in the School Code lists may contain changes or errors and may be updated as necessary.

Errors may also arise either from the primary source or from processing performed by this project.

For uses requiring authoritative or current information, users should always verify the relevant information against the primary source.

---

## Maintenance and Project Information

This dataset is maintained as part of the `open-secondary-data` project.

For project maintainership, contact information, repository-wide policies on terms of use, and design principles, see the [root README](../../README.md).
