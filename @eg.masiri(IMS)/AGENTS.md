# AGENTS.md

Flask app factory project (`masiriSystem`). No git repo, no tests. `requirements.txt` pins the two deps.

## Run

From repo root (the venv is **Windows**-created; there is no Linux python):

```bash
./env/Scripts/python.exe app.py
```

- Serves on `http://127.0.0.1:9999`, debug reloader on (spawns multiple processes).
- Windows-native: `& e:\masiriSystem\projecrt\env\Scripts\python.exe e:/masiriSystem/projecrt/app.py`
- One-click on Windows: double-click `run.bat` — uses the project venv if it works on that PC; otherwise falls back to system python and `pip install -r requirements.txt` first. Once the server answers at `http://127.0.0.1:9999/`, a hidden PowerShell poller (up to ~30s) auto-opens the default browser at `http://localhost:9999/`; a startup crash opens nothing and leaves the traceback in the console.

## WSL ↔ Windows gotchas (important)

- The venv is a Windows venv living under `env/` (`env/Scripts/`, not `env/bin/`). Invoke it as `./env/Scripts/python.exe` from WSL; `python` / `python3` in WSL will not have Flask.
- The dev server binds on the **Windows** side. WSL `curl http://127.0.0.1:9999` returns `000` (connection failure) even when the server is healthy. To test routes over HTTP, use:
  ```bash
  powershell.exe -NoProfile -Command "Invoke-WebRequest -Uri http://127.0.0.1:9999/ -UseBasicParsing"
  ```
- To stop the server from WSL: `taskkill.exe /F /IM python.exe` (kills all Windows python processes — the only reliable way, since the reloader respawns).

## Imports (recurring bug in this repo)

- `app.py` is run **directly as a script**, so it must use the absolute import `from src import create_app`. Relative imports (`from .src import ...`) crash with `ImportError: attempted relative import with no known parent package`.
- Inside `src/`, import blueprint variables explicitly: `from .items import items` (in `src/__init__.py`). Using `from . import items` binds the *module*, causing `AttributeError: module 'src.items' has no attribute 'register'` at `register_blueprint` (module/variable name collision). Never write `from .src import ...` inside `src/`.

## Architecture

- Entry: `app.py` → `create_app()` from `src/__init__.py` → `app.run(debug=True, port=9999)`.
- Blueprints in `src/`: `items.py` (`items`, prefix `/`), `dashboard.py` (`dashboard`, prefix `/`). Add routes with `@items.route(...)` in the module.
- Templates: `src/templates/` — `base.html` (Bootstrap 5 via jsdelivr CDN with SRI hashes, dark theme, design system below), `home.html`, `add_items.html`, `orders.html`.
- `src/mod.py` holds all raw mysql-connector DB functions (no ORM).

## API routing convention (apply to all new functions)

Every mutating/action endpoint lives at `/api/<feature>/<action>` and is a **separate function** from the page route:

- Page route (GET only) renders the template: `/add_items`, `/orders`.
- Action endpoint (POST) does the work, `flash`es a result, then `redirect`s back to the page (post-redirect-get so refresh doesn't re-submit).
- Pattern:
  ```python
  @items.route('/api/<feature>/<action>', methods=["POST"])
  def api_<action>():
      ...call mod.py function...
      flash("...","success" or "danger")
      return redirect("/<feature>")
  ```
- Examples in `items.py`: `/api/add_items` (POST add), `/api/add_items/reset` (POST wipe inventory), `/api/orders/add_order` (POST ava→sold), `/api/orders/refund_order` (POST sold→ref).
- All DB logic goes in `src/mod.py` as small functions (e.g. `mark_item_sold`, `reset_inventory`, `get_inventory_stock`); blueprints only parse input, call one mod function, and flash/redirect. Mod functions that change rows commit and return `cursor.rowcount` so the endpoint knows success vs. "nothing matched".
- HTML forms point their `action` at the `/api/...` endpoint; inputs must carry both `id` (unique) and `name` (what the endpoint reads via `request.values.get`).

## Design system (use for every page/feature)

`base.html` already carries the whole visual identity. New templates **extend it** and fill `{% block title %}`, `{% block content %}`, and optionally `{% block extra_head %}` — never re-add fonts, Bootstrap, or the nav.

Palette (defined as `--ms-*` custom properties on `:root` in `base.html` — reuse the variables, never hardcode hex):

- `--ms-bg: #29313f` page · `--ms-surface: #303b4c` navbar/cards · `--ms-surface-2: #3a465a` inputs/hover · `--ms-hairline: #414d63` borders
- `--ms-ink: #e6ebf2` text · `--ms-ink-dim: #a3aebd` secondary text · `--ms-brass: #d9a441` the only accent · `--ms-brass-bright: #e7bb63` hover · `--ms-on-brass: #2b2314` text on brass

Type: Barlow (body, 400/500/600) + Barlow Semi Condensed (display + nav wordmark, 600/700). Already loaded via Google Fonts in `base.html` — headings pick them up automatically.

Bootstrap: `data-bs-theme="dark"` + `--bs-*` variable overrides in `base.html` theme BS components. Use standard BS components/classes; they inherit the theme. Keep the SRI hashes on any new CDN assets.

Existing utility classes in `base.html`: `.btn-brass` (primary action), `.ms-btn-quiet` (secondary), `.ms-lead` (dim lead text), `.ms-nav-link` (brass underline on hover; set `aria-current="page"` for the active nav item).

Rules for new pages:

- Brass is the **only** accent — one filled brass button per view for the main action; everything else quiet.
- Motion: at most one orchestrated moment per page; always wrap it in a `@media (prefers-reduced-motion: reduce)` kill switch and keep visible `:focus-visible` outlines.
- Avoid generic AI-design tells: no all-caps eyebrow labels, no middle-dot meta strings, no `→` on links/buttons, no soft-grey-shadow card grids, no gradient decoration.
- Copy: sentence case, active voice, CTAs name their action ("Add item", not "Submit").

## Dependencies

- Python 3.14, Flask 3.1.3, mysql-connector-python, openpyxl (Excel export) — installed only in the Windows venv; `requirements.txt` pins all versions. On a new device: `python -m pip install -r requirements.txt` (plus a MySQL server accepting `root`/`root` on `localhost` — credentials are hardcoded in `src/mod.py:db_conn()`). New deps must be installed via `./env/Scripts/python.exe -m pip install <pkg>` and added to `requirements.txt`.
