## Useful links:

Mkdocs: https://www.mkdocs.org/user-guide/writing-your-docs/
Material for Mkdocs: https://squidfunk.github.io/mkdocs-material/

## Set up environment (venv)

Run these from inside the `_afc` dir:

Install `uv`

https://github.com/astral-sh/uv

Create venv

```bash
uv venv
source .venv/bin/activate
```

Sync lockfile

```bash
uv sync
```

## Run locally:
```bash
mkdocs serve
```

## Build site:
```bash
mkdocs build
```