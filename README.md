# enterlabs website

How to edit (no coding needed):
- Website text lives in `content.json` (legal pages in `legal.json`).
- Images live in `public/assets/`.
- Design is in `src/styles.css`, motion in `src/site.js`, page templates in `build.py`.

Ask ChatGPT Codex, Claude or webbie in plain words, e.g. "change the homepage headline to ...".
Every change to `main` updates the free preview automatically (GitHub Actions > "Preview"). To put it on the live site, run GitHub Actions > "Publish to live site" (uses Netlify credits).

## Ready-made HTML
The `dist/` folder holds the finished website as plain HTML, CSS and images. Open `dist/index.html` in a browser, or upload the whole `dist/` folder to any web host.
