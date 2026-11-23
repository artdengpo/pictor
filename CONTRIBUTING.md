# Contributing

English | [Русский](CONTRIBUTING.ru.md)

## Before you start

- Open or search an issue before starting substantial work.
- Keep pull requests focused on one bug or feature.
- Never commit `.env`, API keys, personal photos, or generated private content.

## Development setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest
```

## Style and tests

- Use English names for functions and variables; keep user-facing and Russian comments clear.
- Write public docstrings in English.
- Split logic into focused functions and add tests for filename, image, language, and error behavior.
- Run `pytest -q` before opening a pull request.

## Issues and pull requests

Use the bug or feature issue templates and include exact steps or use cases.
Pull requests should describe the change, verification performed, and screenshots
for any user-visible terminal or documentation change.
