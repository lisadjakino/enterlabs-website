# enterlabs website

How to edit (no coding needed):
- Website text lives in `content.json` (legal pages in `legal.json`).
- Images live in `public/assets/`.
- Design is in `src/styles.css`, motion in `src/site.js`, page templates in `build.py`.

Ask ChatGPT Codex, Claude or webbie in plain words, e.g. "change the homepage headline to ...".
Netlify rebuilds automatically on every change to `main` (build: `python3 build.py`, publish: `dist`).
