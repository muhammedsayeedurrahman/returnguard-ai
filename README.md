# sec_logistics

Returns-fraud detection — Inconsistency Engine + AI Evaluation Engine for the PS2 hackathon.

## Quickstart (Windows / Git Bash)

### 1. Backend

```bash
cd server
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: add GEMINI_API_KEY (Google AI Studio)
python seed.py
uvicorn app.main:app --reload --port 8000
```

Backend at http://localhost:8000 · health check: http://localhost:8000/healthz

### 2. Frontend

```bash
cd client
npm install
npm run dev
```

Frontend at http://localhost:5173

### 3. Demo

Open http://localhost:5173/demo and click the buttons:

- **Run Maya** — legit claim → instant approve
- **Run Priya** — borderline claim → AI Evaluation Engine takes over
- **Run Ring** — burst-submit 4 ring accounts → admin dashboard lights up

## Architecture

See `docs/SYSTEM_DESIGN.md` for components. See `docs/WIN_PLAYBOOK.md` for the pitch.

## Stack

- Backend: Python 3.12 + FastAPI + SQLite + scikit-learn (TF-IDF) + Pillow + Gemini 2.5 Flash
- Frontend: React 18 + Vite + TailwindCSS v4

## Demo Mode

Set `USE_MOCK_VISION=true` in `.env` to bypass external Vision API calls — uses cached fixtures. **Required for offline / unreliable-network demos.**

## License

MIT (hackathon submission)
