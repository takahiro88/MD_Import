# MD_Import - Markdownファイル から Jama への インポートツール

このツールは、Markdownファイルの階層構造を解析し、Jama Connect に要件として自動インポートするPythonスクリプトです。

## 🚀 概要

Markdownファイルの見出し階層を以下のようにJamaのアイテムタイプにマッピングしてインポートします：

- `##` (h2) → **Component**
- `###` (h3) → **Set**  
- `####` (h4) → **Item**
- `#####` (h5) → **Item**（親アイテムの子として作成）

## 📁 ファイル構成

```
MD_Import/
├── MD_Import.py                # メインスクリプト
├── importSetting.yaml          # 設定ファイル
├── sample_requirements.md      # サンプルMarkdownファイル
├── py_jama_rest_client/       # Jama REST API クライアント
└── README.md                   # このファイル
```

## 🔧 必要な環境

### Python要件
- Python 3.12+
- 必要なライブラリ:
  ```
  PyYAML
  markdown
  urllib3
  ```

### Jama Connect要件
- Jama Connect インスタンスへのアクセス
- 適切な権限を持つユーザーアカウント
- プロジェクトIDとアイテムタイプIDの情報

## ⚙️ セットアップ

### 1. 依存関係のインストール

```bash
# 仮想環境の作成（推奨）
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 必要なライブラリのインストール
pip install PyYAML markdown urllib3
```

### 2. 環境変数の設定

#### BASIC認証の場合:
```bash
set AUTH_TYPE=BASIC
set JAMA_URL=https://your-jama-instance.com
set JAMA_USERNAME=your_username
set JAMA_PASSWORD=your_password
```

#### OAuth認証の場合:
```bash
set AUTH_TYPE=OAUTH
set JAMA_URL=https://your-jama-instance.com
set JAMA_CLIENT_ID=your_client_id
set JAMA_CLIENT_SECRET=your_client_secret
```

### 3. 設定ファイルの編集

`importSetting.yaml` を編集して、プロジェクト固有の設定を行います：

```yaml
settings:
    # インポートするMarkdownファイルのパス
    input_file: "C:\\path\\to\\your\\requirements.md"
    
    # JamaプロジェクトID
    project_id: 132
    
    # アイテムタイプID（Item用）
    itemType: 140
```

## 📝 Markdownファイルの準備

### サンプル構造

```markdown
# プロジェクト名

## ユーザー認証システム
認証機能の概要説明

### ログイン機能
ログイン機能セットの説明

#### ログイン画面の表示
具体的な要件の詳細説明

##### ユーザーID入力フィールド
さらに詳細な子要件
```

### ガイドライン

- **見出し階層**: `##`から始めて、最大5レベル（`#####`）まで対応
- **タイトル**: 見出しテキストがJamaアイテムの名前になります
- **説明**: 見出し下の本文がJamaアイテムの説明欄に設定されます
- **画像**: Markdown記法で画像を含めることができます

## 🎯 使用方法

### 基本的な実行

```bash
python MD_Import.py
```

### 実行の流れ

1. **設定読み込み**: `importSetting.yaml`から設定を読み込み
2. **認証**: 環境変数を使用してJamaに接続
3. **Markdown解析**: 指定されたMarkdownファイルを階層構造で解析
4. **Jama作成**: 解析した構造に従ってJamaアイテムを順次作成
5. **完了報告**: 作成結果をコンソールに表示

### 出力例

```
Started JamaAccess initialization
Parsing Markdown file: sample_requirements.md
Found 12 sections
Creating Component: ユーザー認証システム (parent: None)
Created item: ユーザー認証システム (ID: 12345)
Creating Set: ログイン機能 (parent: 12345)
Created item: ログイン機能 (ID: 12346)
...
Import completed!
```

## 📊 Jamaアイテムタイプマッピング

| Markdownレベル | Jamaアイテムタイプ | デフォルトID |
|---------------|------------------|-------------|
| `#` (h1)      | （処理対象外）     | -           |
| `##` (h2)     | Component        | 30          |
| `###` (h3)    | Set              | 31          |
| `####` (h4)   | Item             | 140 (設定可能) |
| `#####` (h5)  | Item（子）        | 140 (設定可能) |

## ⚠️ 注意事項

- **API制限**: Jama APIの制限を考慮して、各作成間に0.5秒の待機時間を設けています
- **エラーハンドリング**: 作成に失敗したアイテムはエラーメッセージで報告されます
- **階層関係**: 親子関係は自動的に設定されます
- **重複作成**: 同じ名前のアイテムでも重複して作成される可能性があります

## 🔍 トラブルシューティング

### よくある問題

**認証エラー**
- 環境変数が正しく設定されているか確認
- Jamaインスタンスの URL に `/` が含まれていないか確認

**ファイルが見つからないエラー** 
- `importSetting.yaml` の `input_file` パスが正しいか確認
- ファイルの文字エンコーディングがUTF-8になっているか確認

**Jamaアイテム作成エラー**
- プロジェクトIDが正しいか確認
- アイテムタイプIDが存在するか確認
- ユーザーに適切な権限があるか確認

## 📞 サポート

問題が発生した場合は、以下の情報を含めて報告してください：

- Pythonバージョン
- エラーメッセージ
- 使用している設定ファイルの内容（認証情報は除く）
- Markdownファイルの構造例

## 📄 ライセンス

このプロジェクトは内部使用のためのツールです。

---

**作成日**: 2026年4月3日  
**バージョン**: 1.0.0
