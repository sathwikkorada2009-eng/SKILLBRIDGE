# SkillBridge

A peer-to-peer learning app built from the supplied SkillBridge prototype. It
includes a FastAPI backend, a responsive browser interface, and the original
command-line menu.

## Run locally

Use Python 3.10 or later:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Run the API tests with:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

To enable the AI assistant and audio notes, set `OPENAI_API_KEY` in the
environment before starting the server. The original CLI is still available
with `python main.py`.

## Deploy

- **Render API:** Create a Blueprint from this repository and use
  [`render.yaml`](./render.yaml). Its free instance uses temporary storage, so
  demo data may reset after a restart or deploy. Configure `SKILLBRIDGE_DATA_FILE`
  to point at persistent storage if the data must be retained.
- **Vercel frontend:** Import the repository and set the project root to
  `frontend`. Once the Render service is live, open the gear/settings control
  and connect the Render service URL. The frontend adds `/api` automatically.
- Configure Render's `CORS_ORIGINS` to the Vercel site origin. Set
  `OPENAI_API_KEY` as a secret in Render; do not commit it.

## Prototype safety

The supplied model identifies users by name and does not authenticate them.
This is suitable only for a synthetic-data demo. Do not publish private
information or real meeting links until authentication, authorization, and
production data storage are added.
