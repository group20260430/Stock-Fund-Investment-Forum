# Backend

Python FastAPI backend for the stock and fund investment forum.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Default API entry: http://localhost:8000
