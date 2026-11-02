# AGENTS.md

deciframe is a song-discovery tool for musicians: search by title/artist,
genre, chords you already know, or a famous chord sequence, and it finds
similar songs. Full description: [README.md](README.md).

## Stack

- Backend: Python 3.9, Flask 3.1, gunicorn. `main.py` loads
  `data/top/dataset_final.csv` into memory once at startup. A SQLite file stores
  the custom chord-sequence catalog; it is not used for songs or genres.
- Frontend: AngularJS 1.4.9 + jQuery, loaded from CDN in `static/index.html`,
  no build step. Legacy, and there's no plan to modernize the stack itself —
  but touching it is no longer off-limits when a task needs it; see
  [docs/adr/0003-lift-frontend-freeze.md](docs/adr/0003-lift-frontend-freeze.md).
- Deploy: local-only via Docker for now. No cloud target has been chosen.

## Run locally

Docker (matches how the app actually ships):

```
docker build -t ciframe .
docker run -p 8080:8080 -v deciframe-data:/data ciframe
```

The `deciframe-data` volume persists `SEQUENCES_DB=/data/deciframe.db` across
container restarts and recreation.

Or a plain virtualenv:

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py        # serves on :5000 instead of :8080
```

With a virtualenv, the sequence database defaults to `instance/deciframe.db`.
Override it with `SEQUENCES_DB` if needed.

## Verify it's up

```
curl http://localhost:8080/generos
curl http://localhost:8080/sequencias
```

Done when `/generos` returns a JSON array of genre names (e.g. `["Rock", "Samba", ...]`) and `/sequencias` returns at least the 6 seeded sequences. If it hangs on startup, it's still parsing the CSV — give it a few seconds.

## Gotchas

- Editing `data/top/*.csv` requires a restart: it's read once at import time, not per-request.
- The sequence catalog lives in SQLite (`SEQUENCES_DB`); deleting the container without a volume loses custom sequences.
- `scripts/check_sequence_regression.py` validates the live matcher against the `SEQ_FAMOSA` tags and baselines.
- Every endpoint returns `json.dumps(...)` as a plain string, not `jsonify` — responses come back `Content-Type: text/html`. This is intentional legacy behavior; changing it is a real API change, not a cleanup.
- Check `docs/adr/` before changing the deploy setup — it has a documented reason for its current state.
