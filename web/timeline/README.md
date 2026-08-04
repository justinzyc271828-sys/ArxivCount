# Interactive timeline (English UI)

Modelrumor-style browser for AI × math milestones. **UI language: English only.**

## Local

```powershell
cd D:\Workspaces\Github\ArxivCount
python -m src.export_web
python -m http.server 8765 --directory web/timeline
```

Open http://127.0.0.1:8765/

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
