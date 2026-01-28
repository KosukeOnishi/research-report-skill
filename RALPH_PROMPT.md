# research-reportスキルをClaude Code形式（SKILL.md）で完成させる

## SKILL.md形式（必須）
```yaml
---
name: research-report
description: 指定トピックについてWebリサーチし、画像・図式を含むPDFレポートを生成
allowed-tools: Bash, Read, Write, Glob, WebSearch, WebFetch
---

(スキルの説明とワークフローをここに記述)
```

## 要件
1. 上記形式でSKILL.mdを作成（YAMLフロントマター + Markdown本文）
2. 既存スクリプト（scripts/fetch_images.py, scripts/create_diagram.py, scripts/generate_pdf.py）を活用
3. テスト実行：「Python Web Framework比較」というトピックでPDFを生成
4. output/test/にサンプルPDFを保存

## 完了条件
以下がすべて満たされたら「SKILL_COMPLETE」と出力して終了：
- SKILL.mdが存在し、正しいYAMLフロントマター形式
- output/test/report.pdfが存在し、0バイトより大きい

## 注意
- .venv/を有効化してからスクリプト実行
- 詰まったら現状を報告して次のイテレーションで改善
