# METFI Backend

FastAPI service for METFI Autonomous Finance Controller.

## Development

```bash
uv venv .venv --python 3.12
uv pip install -e ".[dev]"
uv run pytest -v
uv run uvicorn app.main:app --reload --port 8000
```
