# Research Report Generator

Claude Code用のリサーチレポート生成スキル。WebリサーチからPDF出力まで自動化。

## 機能

- 🔍 **Webリサーチ**: 複数ソースから情報収集
- 📊 **図表生成**: 棒グラフ、円グラフ、統計カード、比較表
- 🖼️ **画像取得**: Web画像のダウンロード・最適化
- 📄 **PDF出力**: プロフェッショナルなレポート生成

## 必要環境

- Python 3.10+
- Claude Code
- Ralph Loop プラグイン（推奨）

## セットアップ

```bash
cd research-report
python -m venv .venv
source .venv/bin/activate
pip install weasyprint pillow requests
```

## 使い方

### Claude Codeから直接実行
```
skills/research-report/SKILL.md を読んで、[トピック]についてレポートを作成して
```

### Ralph Loopで実行（推奨）
```
/ralph-loop:ralph-loop "
skills/research-report/SKILL.md を読んで、[トピック]についてレポートを作成する
" --completion-promise "SKILL_COMPLETE" --max-iterations 15
```

## スクリプト

| スクリプト | 説明 |
|-----------|------|
| `scripts/generate_pdf.py` | Markdown → PDF変換 |
| `scripts/create_diagram.py` | SVG図表生成 |
| `scripts/download_images.py` | Web画像ダウンロード・最適化 |

## 図表タイプ

```bash
# 棒グラフ
python scripts/create_diagram.py --type bar --title "タイトル" --data '[...]' --output chart.svg

# 円グラフ
python scripts/create_diagram.py --type pie --title "タイトル" --data '[...]' --output chart.svg

# 統計カード
python scripts/create_diagram.py --type stats --title "主要指標" --data '[...]' --output stats.svg

# 比較表
python scripts/create_diagram.py --type comparison --title "比較" --data '[...]' --output table.svg
```

## ライセンス

MIT
