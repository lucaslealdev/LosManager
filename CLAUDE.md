# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Los Manager is a desktop management system for "Los Pastelles" (a Brazilian pastelaria/food business), built with Python + CustomTkinter. It handles products, customers, orders, cash register (caixa), reports, and thermal receipt printing. The UI text, variable names, and comments are in Portuguese (pt-BR) — keep new code consistent with that convention.

## Running the app

```
python main.py
```

No virtual environment or dependency manifest is checked in. Required third-party packages (install as needed): `customtkinter`, `Pillow` (`PIL`), `pywin32` (`win32print`, used by `utils/impressora.py`). Standard library only otherwise.

There is no test suite, linter, or formatter configured in this repo.

## Building the Windows executable

```
build.bat
```

This installs PyInstaller, cleans `build/`/`dist/`, and runs `python -m PyInstaller LosManager.spec --clean`. The output is `dist/LosManager/` — that whole folder must be copied together (no Python install needed on the target machine). `LosManager.spec` bundles `assets/` and collects `customtkinter` data files; `win32print`/`win32ui`/`win32con`/`win32timezone` are declared as hidden imports since PyInstaller can't detect them automatically.

If invoking this from Git Bash (not a native Windows shell): run it as `./build.bat < /dev/null`, not `cmd /c build.bat` or `cmd //c build.bat`. Both `cmd /c` forms get mangled by MSYS path conversion of the `/c` flag and silently fail to run the script (either "not recognized" or a no-op interactive `cmd` session) without a nonzero-looking failure that's obvious from the transcript — always check the resulting `dist/LosManager/LosManager.exe` timestamp to confirm a rebuild actually happened. The `< /dev/null` redirect is needed because the script ends with `pause`, which otherwise waits on stdin.

## Architecture

**Entry point**: `main.py` defines `LosManager(ctk.CTk)`, the main window. It builds a left sidebar menu and a right content area. Each menu button swaps the content area's contents by destroying existing widgets (`limpar_area`) and instantiating a screen class into `self.area`. There is no routing/state framework — navigation is just "destroy everything in the frame, build a new one."

**`screens/`**: one module per feature area, each exposing a `ctk.CTkFrame` subclass instantiated by `main.py` (`Dashboard`, `Produtos`, `Clientes`, `Pedidos`, `Caixa`, `Relatorios`, `Configuracoes`). These are self-contained: each screen queries the database directly, builds its own widgets, and owns its own CRUD/dialog logic (typically via `ctk.CTkToplevel` popups and `tkinter.messagebox` for confirmations/errors). There's no shared service/repository layer between screens and the database — SQL lives inline in each screen.

**`database/conexao.py`**: a single `Banco` class wrapping one shared SQLite connection, instantiated once as the module-level singleton `banco` and imported everywhere (`from database.conexao import banco`). It auto-creates all tables (`categorias`, `produtos`, `clientes`, `pedidos`, `itens_pedido`, `caixa`, `movimentos_caixa`, `enderecos_cliente`) on construction, and exposes generic helpers: `executar` (write, auto-commits), `executar_sem_commit`/`commit`/`rollback` (manual transactions, for multi-statement writes that must be all-or-nothing — see `Pedidos.gravar_pedido()`), `buscar` (fetchall), `buscar_um` (fetchone), `ultimo_id` (lastrowid). Screens call these directly with raw SQL rather than going through an ORM. The `configuracoes` key/value table is created lazily by `utils/config.py` instead of `Banco.criar_tabelas`.

**Schema migrations**: there's no migration framework — `Banco.criar_tabelas()` just runs `CREATE TABLE IF NOT EXISTS` for everything, every startup. When a table needs one-time data migration from an older shape (e.g. `enderecos_cliente`, added to let a client have multiple addresses instead of one set of address columns on `clientes`), the pattern is: check whether the new table already existed *before* creating it, and if not, run a one-time migration copying data out of the old columns/shape. The old columns are left in place afterward (not dropped) — cheaper and safer than an `ALTER TABLE ... DROP COLUMN`, and nothing reads them going forward. Follow this same check-then-migrate-once pattern for future schema changes.

**`utils/config.py`**: persistent app settings stored as key/value rows in the `configuracoes` table (store name/address/phone, printer name, paper width) — this exists so store/printer info doesn't need to be hardcoded per machine. Also owns the frozen-vs-source path resolution used throughout the app:
- `caminho_base()` — folder for *external* files (the SQLite `.db`), which intentionally sits next to the `.exe`, not bundled inside it.
- `caminho_recursos()` / `caminho_asset()` — folder for files *bundled* into the PyInstaller package (assets like icons/logos), resolved via `sys._MEIPASS` when frozen.

`database/conexao.py` has its own near-identical `_caminho_base()` for the same frozen-vs-source distinction — keep both in sync if that logic changes.

**`utils/tema.py`**: the single source of truth for brand colors (`COR_LARANJA`, `COR_TEXTO`, etc.) and `ttk.Treeview` styling. Also defines a "compatibility" block of old color name aliases (`COR_MARROM`, `COR_SALMAO`, ...) kept so older screen code doesn't break — prefer the current names in new code.

**`utils/impressora.py`**: builds and sends ESC/POS raw byte commands to a Windows-installed thermal printer via `win32print` (RAW spooler job), independent of printer brand. `montar_cupom()` composes the receipt bytes (store header + logo bitmap + items + totals) from plain dicts; `imprimir_cupom()` sends it, pulling printer name/paper width from `utils/config.py` if not passed explicitly. Paper width in chars: 32 = 58mm, 48 = 80mm.

**External network call**: `screens/clientes.py` looks up addresses by CEP (Brazilian postal code) via the public ViaCEP API (`urllib.request` in a background `threading.Thread`, JSON parsed with `json.loads`) so the UI doesn't freeze while waiting on the network.

## Conventions to follow

- Screen classes follow a consistent internal layout: `__init__` calls a sequence of `montar_*`/`criar_*` builder methods; section breaks are marked with `# ====...====` comment banners.
- Database access is inline raw SQL through the shared `banco` singleton — do not introduce an ORM or a new connection; add queries directly in the relevant screen (or `utils/config.py`-style module for settings).
- Path resolution must always go through `utils/config.py`'s `caminho_base`/`caminho_recursos`/`caminho_asset` helpers (or the equivalent in `database/conexao.py`) so both dev (`python main.py`) and frozen (`.exe`) execution keep working.
- New persistent settings belong in the `configuracoes` key/value table via `utils/config.py`, not as new hardcoded constants.
