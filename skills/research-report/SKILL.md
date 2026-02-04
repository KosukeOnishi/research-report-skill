---
name: research-report
description: 指定トピックについてWebリサーチし、データ図表を含むエキスパートレベルPDFレポートを生成。トリガー：「リサーチレポート」「調査報告書」「〜についてレポート作成」「PDF作成」「比較レポート」
---

# Research Report Generator

指定トピックのWebリサーチ → データ図表生成 → PDF出力を自動化。
**エキスパートレベル**のレポートを生成し、外部リサーチ不要で意思決定可能なクオリティを目指す。

## トリガー例
- 「Python Web Frameworkの比較レポートを作成して」
- 「AIツールについてリサーチレポート作成」
- 「〜をPDFでまとめて」
- 「2025年デザイントレンドのレポート」

## 実行手順

### 1. 環境準備
```bash
cd ~/clawd/skills/research-report
source .venv/bin/activate
```

### 2. 出力ディレクトリ作成
```bash
mkdir -p output/{topic}/images
```

### 3. Webリサーチ（徹底的に）

`WebSearch`と`WebFetch`でトピックを調査：
- **最低5つ以上の一次ソース**を参照
- 具体的な**統計データ・パーセンテージ**を収集
- **企業名・製品名・人物名**の実例を取得
- 各トレンドについて**特徴・事例・適用分野**を記載
- **市場規模・成長率（CAGR）**を把握

**検索クエリ例:**
- `{topic} statistics data 2025`
- `{topic} market size growth rate`
- `{topic} survey percentage adoption rate`

### 4. Web画像の取得と選別（UIトレンド等のビジュアル系トピックの場合）

トピックがデザイン、UI/UX、ビジュアル系の場合は、Web記事から実例画像を取得する。

#### Step 4.1: 画像URL収集
`WebFetch`で記事を取得し、画像URLを抽出：
```
WebFetch で記事を取得
プロンプト: "Extract ALL image URLs (img src, data-src, srcset) showing UI examples, design screenshots. Format as JSON array."
```

#### Step 4.2: 画像ダウンロード・最適化
```bash
# URLリストをファイルに保存
# output/{topic}/image_urls.txt

# ダウンロードと最適化（PNG→JPG変換、800px幅、85%品質）
python scripts/download_images.py \
  --url-file output/{topic}/image_urls.txt \
  --pool-dir output/{topic}/images/pool \
  --output-dir output/{topic}/images/optimized
```

#### Step 4.3: 画像選別（Claude自身が視覚確認）
`Read`ツールで各画像を確認し、以下の基準で選別：

**採用:**
- UIの実例・デザインスクリーンショット
- データ図表・インフォグラフィック
- 製品UIの具体例

**却下:**
- 抽象的なイメージ画像
- ストック写真
- ロゴ・アイコンのみ
- 著者写真

```bash
# 採用画像をselectedディレクトリにコピー
cp optimized/xxx.jpg selected/01_description.jpg
```

#### Step 4.4: クリーンアップ
```bash
rm -rf output/{topic}/images/pool
```

#### Step 4.5: 画像取得が失敗した場合（重要！）

**絶対に諦めない。** レート制限・403・404で画像が取得できなかったら、以下の代替手段を順番に試す：

**代替手段1: Playwright（MCP）でブラウザ経由で取得**
```
# Playwright MCPを使ってGoogle画像検索
mcp__playwright__browser_navigate url:"https://www.google.com/search?q={人物名}+portrait&tbm=isch"
mcp__playwright__browser_screenshot
# 画像URLを抽出してダウンロード
```

**代替手段2: 別のソースを探す**
- Getty Images（プレビュー画像）
- Britannica
- 公式サイト・レコードレーベル
- 大学・音楽院のアーカイブ
- 新聞社のアーカイブ

**代替手段3: 別の検索クエリで再試行**
```
{人物名} photo
{人物名} portrait
{人物名} musician
{人物名} violinist image
```

**代替手段4: curlで直接ダウンロード**
```bash
curl -L -o output/{topic}/images/{name}.jpg "https://..." \
  -H "User-Agent: Mozilla/5.0 ..."
```

**代替手段5: 時間を置いて再試行**
レート制限の場合、30秒〜1分待ってから再試行。

**最終手段: 写真がないことを明記**
どうしても取得できない場合のみ、レポート内で「写真は入手不可」と明記し、その人物の説明は文章で補う。ただしこれは最後の手段。

### 5. データ図表生成

**自作図表（必須）:**
- 棒グラフ（統計比較）
- 円グラフ（シェア・構成比）
- 統計カード（主要指標のハイライト）
- 比較表

**画像の判定基準:**
「その画像だけで何かがわかるか？」
「削除しても内容が変わらないなら不要」

#### 図表生成スクリプト

**棒グラフ（bar）:**
```bash
python scripts/create_diagram.py --type bar \
  --title "タイトル" \
  --data '[{"label": "項目A", "value": 75, "unit": "%"}, {"label": "項目B", "value": 50, "unit": "%"}]' \
  --output output/{topic}/images/chart_name.svg \
  --color "#2563eb"
```

**円グラフ（pie）:**
```bash
python scripts/create_diagram.py --type pie \
  --title "タイトル" \
  --data '[{"label": "カテゴリA", "value": 60}, {"label": "カテゴリB", "value": 40}]' \
  --output output/{topic}/images/pie_chart.svg
```

**統計カード（stats）:**
```bash
python scripts/create_diagram.py --type stats \
  --title "主要指標" \
  --data '[{"label": "ROI", "value": "9,900%", "description": "投資対効果"}]' \
  --output output/{topic}/images/key_stats.svg
```

**比較表（comparison）:**
```bash
python scripts/create_diagram.py --type comparison \
  --title "比較表タイトル" \
  --data '[{"name": "製品A", "price": "$100", "feature": "高速"}, {"name": "製品B", "price": "$50", "feature": "安価"}]' \
  --output output/{topic}/images/comparison.svg
```

### 5. レポート本文作成

`output/{topic}/content.md`にMarkdownで執筆。画像は相対パスで参照：

```markdown
# {topic}リサーチレポート

## TL;DR（5つの重要ポイント）

1. **ポイント1**: 具体的な数字・事例を含む説明
2. **ポイント2**: ...
3. **ポイント3**: ...
4. **ポイント4**: ...
5. **ポイント5**: ...

---

## エグゼクティブサマリー

[3段落で概要。市場規模、主要トレンド、ビジネスインパクトを含む]

![主要指標](images/key_stats.svg)
*図1: {topic}の主要指標*

---

## 1. セクション名

### サブセクション

**主要データ:**
- XX%のユーザーが〜
- 市場規模$XX億

![データ図表](images/chart1.svg)
*図2: 〜を示すグラフ*

**事例:**
- **企業A**: 具体的な活用方法と成果
- **企業B**: 具体的な成果

> 「引用文」— 出典者名

---

## 市場規模と成長予測

| 市場 | 2024年 | 2030年 | CAGR |
|------|--------|--------|------|
| セグメントA | $X.XB | $X.XB | X.X% |
| セグメントB | $X.XB | $X.XB | X.X% |

![市場成長予測](images/market_growth.svg)
*図3: 市場規模の推移予測*

---

## 結論と推奨アクション

### 主要インサイト

1. **発見1**
   - 詳細説明
   - ビジネスへの影響

2. **発見2**
   - 詳細説明
   - 推奨アクション

### 次のステップ
- [ ] アクション1
- [ ] アクション2

---

## 出典

### 一次ソース
1. 出典名. "タイトル." URL
2. ...

### 画像クレジット
- 全図表：Claude（Anthropic）により生成されたオリジナルデータビジュアライゼーション
```

### 6. PDF生成

```bash
python scripts/generate_pdf.py \
  --title "{topic}リサーチレポート" \
  --content output/{topic}/content.md \
  --output output/{topic}/report.pdf \
  --author "Claude (Anthropic)"
```

**注意**:
- `--content`にはMarkdownファイルのパスを指定
- 画像は自動的にMarkdown内の`![](images/xxx.svg)`から検出・埋め込み
- テーブル（|で囲まれた表）は自動でHTMLテーブルに変換

### 7. 品質チェック

生成されたPDFを**Read toolで確認**：

**画像チェック:**
- [ ] 全ての画像がデータ・図表（棒グラフ、円グラフ、統計カード）
- [ ] スクリーンショットや製品写真が含まれていない
- [ ] 各画像が「情報を伝えている」

**情報チェック:**
- [ ] このレポートを上司に出せるか？
- [ ] 追加調査なしで意思決定できるか？
- [ ] 外部リサーチ不要レベルか？

**体裁チェック:**
- [ ] フォント読みやすいか？
- [ ] テーブルが正しく表示されているか？
- [ ] プロが作ったように見えるか？

### 8. ユーザーへ送付
生成されたPDFを`message action:send filePath:...`でDiscordに送信。

## 出力構成
```
output/{topic}/
├── images/
│   ├── pool/              # 一時ダウンロード（処理後削除）
│   ├── optimized/         # 最適化済み画像
│   ├── selected/          # 採用画像（リネーム済み）
│   │   ├── 01_spatial_design.jpg
│   │   ├── 02_dark_mode_example.png
│   │   └── ...
│   ├── chart_stats.svg    # 自作図表
│   ├── chart_pie.svg
│   └── chart_bar.svg
├── image_urls.txt         # 収集した画像URL
├── content.md             # レポート本文（Markdown）
└── report.pdf             # 最終成果物
```

## 品質基準

### 情報の充足性
- [ ] 外部リサーチ不要なレベルの詳細
- [ ] 具体的な統計データ（%、$、件数）
- [ ] 実在の企業・製品名を挙げた事例
- [ ] 引用元が明記された発言
- [ ] 市場規模・成長率（CAGR）の記載

### 画像の厳格基準

**ビジュアル系トピック（UI/UX、デザイン等）の場合:**
- [ ] Web画像 ≥ 3枚（実際のUI例・デザイン例）
- [ ] 自作図表 ≥ 2枚（create_diagram.pyで作成）
- [ ] 合計 ≥ 5枚
- [ ] 全画像が情報を伝えている（装飾目的は不可）
- [ ] PDFサイズ ≤ 20MB

**データ系トピックの場合:**
- [ ] **全ての画像がデータ・図表**（棒グラフ、円グラフ、統計カード、比較表）
- [ ] **スクリーンショット・製品写真は禁止**
- [ ] 画像にキャプションあり
- [ ] create_diagram.pyで生成したSVGを使用

### 体裁
- [ ] サンセリフフォント、16px以上
- [ ] 十分な余白
- [ ] 見出しの階層が明確
- [ ] 引用がブロック形式で整形
- [ ] テーブルが正しく表示

## 依存環境
- Python 3.10+ with .venv
- weasyprint（PDF生成）
- Pillow（画像処理）
- requests（画像ダウンロード）
- scripts/create_diagram.py（図表生成）
- scripts/generate_pdf.py（PDF生成）
- scripts/download_images.py（Web画像取得・最適化）

## スクリプトの機能

### download_images.py
Web画像のダウンロードと最適化:
- URLリストから画像を一括ダウンロード
- PNG → JPG変換（透明度がない場合）
- 最大幅800pxにリサイズ
- JPEG品質85%で圧縮
- 小さすぎる画像（200px未満）は自動除外

```bash
python scripts/download_images.py \
  --url-file image_urls.txt \
  --pool-dir images/pool \
  --output-dir images/optimized \
  --max-width 800 \
  --quality 85 \
  --json
```

### create_diagram.py
図表タイプ:
- `bar`: 横棒グラフ（統計比較に最適）
- `pie`: 円グラフ（シェア・構成比に最適）
- `stats`: 統計カード（主要指標のハイライト）
- `comparison`: 比較表（複数項目の機能比較）
- `flowchart`: フローチャート（プロセス説明）

### generate_pdf.py
機能:
- Markdown → HTML → PDF変換
- 画像の自動埋め込み（data URI）
- テーブルのHTML変換
- プロフェッショナルなスタイリング
