# GitHub Profile AI Reviewer

FastAPI service that rates a public GitHub user profile out of 100.

The API accepts a GitHub username and returns a `rating_score`, developer level, language breakdown, contribution signals, streak data, and model metadata.

## Folder Structure

```text
app/
  main.py              FastAPI app entrypoint and static frontend serving
  api/                 HTTP routes for health checks and profile analysis
  schemas.py           Request and response models
  service.py           Application service layer
  ai/                  Embedding and scoring logic
  clients/             GitHub API clients and queries
  core/                Settings and logging
  graph/               Active analysis workflow
  static/index.html    Browser API console
backend/               Legacy LangGraph prototype pipeline
experiments/           Standalone prototype files
scripts/               Developer utilities and CLI helpers
```

## Token Behavior

`GITHUB_TOKEN` is optional.

When `GITHUB_TOKEN` is set, the service uses GitHub GraphQL for richer profile and contribution data. When it is empty, users can still rate any public GitHub username through GitHub's public REST API. Public REST mode is limited by GitHub's unauthenticated rate limits and cannot see private contribution data.

If you hit GitHub's public rate limit, add a valid token to `.env` and restart the server. Public mode keeps its request count low and caches successful GitHub responses for `GITHUB_CACHE_TTL_SECONDS` to avoid wasting quota during repeated tests.

## Environment

Copy `.env.example` to `.env` and adjust only what you need:

```env
GITHUB_TOKEN=
GITHUB_API_URL=https://api.github.com/graphql
GITHUB_REST_API_URL=https://api.github.com
GITHUB_PUBLIC_REPO_LIMIT=20
GITHUB_FETCH_COMMIT_COUNTS=false
GITHUB_CACHE_TTL_SECONDS=900
APP_HOST=0.0.0.0
APP_PORT=8000
SCORING_BACKEND=heuristic
```

Keep `SCORING_BACKEND=heuristic` unless you have trained model weights. The neural backend is experimental.

## Run Locally

On Windows PowerShell, use a project virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If `py -3.12` is not installed, use your available Python launcher version:

```powershell
py -0p
```

The default requirements start the API with deterministic fallback embeddings. Optional ML packages are separate:

```powershell
python -m pip install -r requirements-ml.txt
```

On macOS/Linux:

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open the browser console UI:

```text
http://localhost:8000/
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

The API and `index.html` console will be available on `http://localhost:${APP_PORT:-8000}`.

Useful deployment commands:

```bash
docker compose ps
docker compose logs -f api
docker compose down
```

For a cloud VM, install Docker, clone the repo, create `.env`, then run the same `docker compose up --build -d` command. If you deploy behind a domain or reverse proxy, forward public traffic to container port `8000`.

## Use The API In `index.html`

The frontend at `app/static/index.html` calls the API with `fetch`:

```html
<script>
async function analyze(username) {
  const response = await fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Analyze request failed");
  }

  return response.json();
}
</script>
```

Use a full base URL only when the HTML is hosted somewhere else:

```js
fetch("https://your-domain.com/analyze", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "octocat" })
});
```

## Response Fields

- `rating_score`: main score from 0 to 100.
- `hiring_readiness_score`: compatibility alias for the same 0 to 100 score.
- `public_activity.public_commits`: public commits counted for the user.
- `public_activity.public_prs_created`: public pull requests created by the user.
- `model_info.data_source`: `graphql` when a server token is configured, otherwise `rest-public`.

In `rest-public` mode, GitHub exposes these counts from recent public events only. With authenticated GraphQL mode, the counts come from GitHub's contribution totals.
