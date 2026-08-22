# Open Secondary Data

`open-secondary-data` は、公開されている一次情報源や各種資料をもとに、再利用しやすい形式へ整理・構造化した**二次データ（secondary data）**を提供するためのリポジトリです。

単にデータを転載・集積するのではなく、**そのデータがどの一次情報源に基づき、どのような処理を経て作成されたのかを確認できること**を重視します。

[English follows Japanese.](#english)

---

## 日本語

## 基本方針

本リポジトリでは、次の原則に基づいてデータを管理します。

### 1. 一次情報源を明示する

各データセットには、可能な限り次の情報を記録します。

- 一次情報源の名称
- 作成者・公開者
- 公開元URL
- 公開日・基準日・版
- 取得日
- 利用条件
- 二次データ作成時に行った加工・変換

これらはREADME等による人間向けの説明に加え、可能なものについては `metadata.yaml` 等による機械可読な形式でも記録します。

### 2. 一次情報と二次情報を区別する

本リポジトリで提供するデータは、原則として一次情報源そのものではありません。

一次情報源から取得したデータについて、形式変換、正規化、統合、項目整理その他の処理を行った場合は、その内容を明示します。

利用にあたっては、必要に応じて本リポジトリに収録された二次データだけでなく、記載された一次情報源も確認してください。

### 3. 主題を単位として管理する

リポジトリの第一階層には、データ形式や処理方法ではなく、利用者が情報を探す際の単位となる**主題領域（domain）**を配置します。

例：

```text
open-secondary-data/
├── school-codes-jp/
├── tea/
└── ...
````

各主題領域の中で、必要に応じてデータセットや下位の主題領域を定義します。

### 4. 階層の深さを形式的に統一しない

すべての主題領域について、同じ深さのディレクトリ構造を要求しません。

データの性質、分類、利用単位などに基づいて階層化し、**その階層を設ける意味と分類基準を当該階層のREADMEに記述します。**

そのため、単一のデータセットで完結する主題領域と、複数階層から構成される主題領域が同じリポジトリ内に共存する場合があります。

### 5. 主題固有のデータと処理は、その主題内で完結させる

特定のデータセットだけで使用するデータ、一次情報源、処理スクリプト、更新レポート等は、原則としてそのデータセットのディレクトリ内で管理します。

例：

```text
school-codes-jp/
└── mext-school-codes/
    ├── README.md
    ├── data/
    ├── sources/
    ├── scripts/
    └── reports/
```

複数の主題領域で共通して利用する必要が生じたものについては、必要になった時点でリポジトリ共通の領域へ分離します。

### 6. ディレクトリ名には lowercase kebab-case を使用する

ディレクトリ名は、原則としてすべて小文字とし、複数の単語はハイフン（`-`）で接続します。

例：

```text
school-codes-jp
mext-school-codes
```

特定の国・地域の制度に限定されるデータについては、必要に応じて国・地域を識別するコードを付与します。

### 7. 自動処理と人間による確認を組み合わせる

取得・形式変換・正規化・差分検出など、再現可能な処理については、可能な限りスクリプトやGitHub Actions等による自動化を行います。

一方、一次情報源の変更、データ構造の変更、意味上の判断を伴う更新などについては、必要に応じて人間による確認を行います。

自動化そのものを目的とせず、**データの来歴と処理過程を確認・再現できること**を優先します。

### 8. READMEは日本語・英語の順で記述する

READMEは、原則として**日本語を先に記述し、その内容に対応する英語版を後置**します。

日本語を本リポジトリにおける説明の原文とし、英語版は日本語版の内容に対応させます。

一次情報源に含まれる固有名称、制度名称、資料名等については原文を尊重し、必要に応じて英語による説明を付記します。

### 9. 管理情報は一元管理し、各READMEから参照できるようにする

本リポジトリの管理者、問い合わせ先およびリポジトリ全体に関する情報は、ルートの `README.md` を正本として管理します。

各主題領域およびデータセットのREADMEには、これらの情報を重複して記載せず、ルートの `README.md` への参照を記載します。

これにより情報の一元管理を行うとともに、個別の主題領域やデータセットへ直接アクセスした利用者からも、管理主体およびプロジェクト全体の方針を確認できるようにします。

---

## ディレクトリ構成

各主題領域の内部構造は、そのデータの性質に応じて定義します。

代表的なディレクトリ名は次のとおりです。

| ディレクトリ     | 役割                          |
| ---------- | --------------------------- |
| `data/`    | 整理・構造化した二次データ               |
| `sources/` | 二次データの根拠となる一次情報源            |
| `scripts/` | データの取得・変換・正規化・検証等に使用するスクリプト |
| `reports/` | 更新・差分・検証等に関するレポート           |

これらのディレクトリをすべてのデータセットに必須とはしません。必要性と役割が明確な場合に設置します。

---

## 利用条件

本リポジトリには、複数の一次情報源に基づく二次データが収録されます。そのため、**リポジトリ全体に一律の利用条件は設定していません。**

各データセットの利用条件は、それぞれのREADMEおよびメタデータに記載された一次情報源の利用条件を確認してください。

一次情報源に著作権、ライセンス、利用規約その他の利用条件が設定されている場合、本リポジトリの利用者もそれらの条件に従う必要があります。

---

## 管理・問い合わせ

本リポジトリは、**小松崎 浩司（Hiroshi Komatsuzaki）** が管理しています。

データの誤り、一次情報源との不一致、出典・利用条件に関する指摘、データセットに関する質問・提案等については、本リポジトリの **GitHub Issues** からお知らせください。

本リポジトリで提供する二次データについての問い合わせは、本リポジトリの管理者へお願いします。一次情報源の内容そのものについては、各データセットに記載された一次情報源の提供機関へ確認してください。

### Maintainer

**小松崎 浩司 / Hiroshi Komatsuzaki**

* GitHub: `@kojikomatsuzaki`
* researchmap: [https://researchmap.jp/kojikomatsuzaki](https://researchmap.jp/kojikomatsuzaki)

### Repository

`kojikomatsuzaki/open-secondary-data`

---

## このリポジトリについて

本リポジトリは、一次情報を代替することを目的としたものではありません。

公開情報を再利用しやすい形に整理するとともに、**二次情報から一次情報源へ遡ることのできるデータ環境**を構築することを目的としています。

---

# English

`open-secondary-data` is a repository for providing **secondary data** that has been organized and structured into reusable formats based on publicly available primary sources and other materials.

Rather than simply reproducing or aggregating data, this repository emphasizes **traceability: users should be able to determine which primary sources the data is based on and what processes were applied to create the secondary data.**

---

## Principles

This repository is managed according to the following principles.

### 1. Identify primary sources

For each dataset, the following information is recorded whenever possible:

* Title of the primary source
* Creator or publisher
* Source URL
* Publication date, reference date, or edition
* Retrieval date
* Terms of use
* Transformations or modifications performed when creating the secondary data

In addition to human-readable documentation such as README files, this information is recorded in machine-readable formats such as `metadata.yaml` whenever possible.

### 2. Distinguish primary sources from secondary data

The data provided in this repository is generally not the primary source itself.

When data obtained from a primary source is converted, normalized, integrated, reorganized, or otherwise processed, the nature of those transformations is documented.

Users should consult the identified primary sources when necessary rather than relying solely on the secondary data provided in this repository.

### 3. Organize the repository by subject domain

The first directory level is organized by **subject domain**, reflecting how users are likely to look for information, rather than by data format or processing method.

Example:

```text
open-secondary-data/
├── school-codes-jp/
├── tea/
└── ...
```

Datasets and additional subject subdivisions may be defined within each domain as necessary.

### 4. Do not impose a uniform directory depth

Subject domains are not required to use directory structures of identical depth.

Directories are subdivided according to the nature, classification, and intended use of the data. **The purpose of each level and the criteria used for subdivision must be documented in the README for that level.**

As a result, a subject domain containing a single dataset and another domain containing multiple hierarchical levels may coexist within the same repository.

### 5. Keep subject-specific data and processes within their subject

Data, primary-source materials, processing scripts, update reports, and other resources used only by a particular dataset should, in principle, be maintained within that dataset's directory.

Example:

```text
school-codes-jp/
└── mext-school-codes/
    ├── README.md
    ├── data/
    ├── sources/
    ├── scripts/
    └── reports/
```

Resources that become genuinely shared across multiple subject domains may be separated into a repository-wide common area when such a need arises.

### 6. Use lowercase kebab-case for directory names

Directory names should, in principle, use lowercase letters, with multiple words separated by hyphens (`-`).

Examples:

```text
school-codes-jp
mext-school-codes
```

For datasets institutionally limited to a particular country or region, an appropriate country or regional identifier may be appended when necessary.

### 7. Combine automated processing with human review

Reproducible processes such as data retrieval, format conversion, normalization, and change detection should be automated using scripts, GitHub Actions, or similar tools whenever practical.

Changes to primary sources, data structures, or updates requiring semantic judgment may be subject to human review.

Automation is not an end in itself. Priority is given to ensuring that **the provenance and processing history of the data can be examined and reproduced.**

### 8. Write README documentation in Japanese followed by English

README files should, in principle, present **the Japanese text first, followed by a corresponding English version**.

Japanese serves as the source text for repository documentation, and the English version should correspond to the Japanese content.

Original names of institutions, systems, documents, and other terms appearing in primary sources should be preserved, with English explanations added when appropriate.

### 9. Maintain project information in one place and reference it from each README

Information about repository maintainership, contact information, and repository-wide policies is maintained in the root `README.md` as the authoritative source.

README files for individual subject domains and datasets should reference the root `README.md` rather than duplicating this information.

This approach maintains a single source of project information while ensuring that users who access an individual subject domain or dataset directly can still identify the project maintainer and repository-wide policies.

---

## Directory Structure

The internal structure of each subject domain is defined according to the nature of its data.

Typical directory names include:

| Directory  | Purpose                                                                                   |
| ---------- | ----------------------------------------------------------------------------------------- |
| `data/`    | Organized and structured secondary data                                                   |
| `sources/` | Primary sources on which the secondary data is based                                      |
| `scripts/` | Scripts used for retrieval, conversion, normalization, validation, and related processing |
| `reports/` | Reports concerning updates, differences, validation, and related processes                |

Not every dataset is required to contain all of these directories. They should be created only when their purpose and necessity are clear.

---

## Terms of Use

This repository contains secondary data derived from multiple primary sources. Therefore, **no single set of terms of use is applied to the repository as a whole.**

For each dataset, users should consult the terms of use of the primary sources identified in the corresponding README and metadata.

Where copyright, licenses, terms of service, or other conditions apply to a primary source, users of this repository are responsible for complying with those conditions.

---

## Maintenance and Contact

This repository is maintained by **小松崎 浩司 (Hiroshi Komatsuzaki)**.

Please use **GitHub Issues** to report data errors, discrepancies with primary sources, concerns regarding attribution or terms of use, or questions and suggestions concerning individual datasets.

Questions concerning secondary data provided by this repository should be directed to the repository maintainer. Questions concerning the content of a primary source itself should be directed to the organization identified as the source provider for the relevant dataset.

### Maintainer

**小松崎 浩司 / Hiroshi Komatsuzaki**

* GitHub: `@kojikomatsuzaki`
* researchmap: [https://researchmap.jp/kojikomatsuzaki](https://researchmap.jp/kojikomatsuzaki)

### Repository

`kojikomatsuzaki/open-secondary-data`

---

## About This Repository

This repository is not intended to replace primary sources.

Its purpose is to organize publicly available information into reusable forms while building **a data environment in which users can trace secondary data back to its primary sources.**
