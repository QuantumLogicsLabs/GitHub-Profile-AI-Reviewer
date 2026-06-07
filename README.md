# GitHub Profile AI Reviewer

FastAPI service that rates a public GitHub user profile out of 100.

The API accepts a GitHub username and returns a `rating_score`, developer level, language breakdown, contribution signals, streak data, and model metadata.

## Token Behavior

`GITHUB_TOKEN` is optional.

When `GITHUB_TOKEN` is set, the service uses GitHub GraphQL for richer profile and contribution data. When it is empty, users can still rate any public GitHub username through GitHub's public REST API. Public REST mode is limited by GitHub's unauthenticated rate limits and cannot see private contribution data.

## Environment

Copy `.env.example` to `.env` and adjust only what you need:

```env
GITHUB_TOKEN=
GITHUB_API_URL=https://api.github.com/graphql
GITHUB_REST_API_URL=https://api.github.com
GITHUB_PUBLIC_REPO_LIMIT=30
GITHUB_FETCH_COMMIT_COUNTS=true
APP_HOST=0.0.0.0
APP_PORT=8000
SCORING_BACKEND=heuristic
```

Keep `SCORING_BACKEND=heuristic` unless you have trained model weights. The neural backend is experimental.

## Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Request a rating:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"username":"octocat"}'
```

## Deploy With Docker

```bash
docker compose up --build -d
```

The API will be available on `http://localhost:${APP_PORT:-8000}`.

## Response Fields

- `rating_score`: main score from 0 to 100.
- `hiring_readiness_score`: compatibility alias for the same 0 to 100 score.
- `model_info.data_source`: `graphql` when a server token is configured, otherwise `rest-public`.
