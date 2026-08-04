# Interactive timeline

Modelrumor-style browser for AI × math milestones.

| Language | Path | Live |
|----------|------|------|
| English | `./` (this folder) | […/ArxivCount/](https://justinzyc271828-sys.github.io/ArxivCount/) |
| **中文** | [`./zh/`](./zh/) | […/ArxivCount/zh/](https://justinzyc271828-sys.github.io/ArxivCount/zh/) |

Chinese UI + event copy is built by `python scripts/build_zh_site.py`.

## Local

```powershell
cd D:\Workspaces\Github\ArxivCount
python -m src.export_web
python scripts/build_zh_site.py
python -m http.server 8765 --directory web/timeline
```

Open http://127.0.0.1:8765/ (EN) or http://127.0.0.1:8765/zh/ (中文)

Controls: **← / →** keys, on-screen buttons, click rail ticks, swipe on card.

## GitHub Pages

1. Push repo (or copy this folder into `justinzyc271828-sys.github.io/arxivcount/`)
2. Enable Pages on `/docs` or `/` (root) depending on layout
3. For project pages from this repo: set Pages source to `web/timeline` if supported, or mirror files to `/docs`

After data updates:

```powershell
python -m src.denominator --skip-fetch   # if math totals cached
python -m src.timeline
python -m src.export_web
```
