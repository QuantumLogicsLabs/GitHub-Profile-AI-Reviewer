# Deployment Guide: Hugging Face Spaces

This guide deploys the FastAPI app as a Hugging Face Docker Space.

Hugging Face Spaces supports Docker apps, and a Docker Space is configured by adding `sdk: docker` to the YAML block at the top of the Space `README.md`. Docker Spaces commonly expose port `7860`; the app, Dockerfile, and Space metadata must all use the same port.

Official references:

- Hugging Face Docker Spaces: https://huggingface.co/docs/hub/main/spaces-sdks-docker
- Hugging Face Spaces overview: https://huggingface.co/docs/hub/main/spaces-overview

## What Gets Deployed

The Hugging Face Space should deploy the backend API and built-in analyzer UI:

- `GET /` serves `app/static/index.html`
- `GET /health` returns API health
- `POST /analyze` rates a GitHub username

The separate React documentation website in `website/` can be deployed separately as a static site. The Space deployment described here focuses on the FastAPI app.

## Prerequisites

1. A Hugging Face account.
2. Git installed locally.
3. Optional but recommended: a valid GitHub token for higher API limits.

Create a GitHub token and save it as a Hugging Face Space secret named:

```text
GITHUB_TOKEN
```

Public/no-token mode works, but GitHub rate limits unauthenticated requests heavily.

## Create The Space

1. Go to https://huggingface.co/spaces
2. Click **Create new Space**.
3. Choose an owner and Space name.
4. Select **Docker** as the SDK.
5. Choose public or private visibility.
6. Create the Space.

## Space README Metadata

In the Hugging Face Space repository, the top of `README.md` should include:

```yaml
---
title: GitHub Profile AI Reviewer
emoji: 🧪
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
---
```

The important lines are:

```yaml
sdk: docker
app_port: 7860
```

## Hugging Face Dockerfile

Hugging Face expects the app to listen on the configured Space port. Use this Dockerfile for the Space:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOST=0.0.0.0
ENV APP_PORT=7860

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

Why this differs from local Docker:

- Hugging Face Docker Spaces commonly expose `7860`.
- The production API does not require `torch` or `transformers`; default `requirements.txt` is enough.
- `requirements-ml.txt` is optional and should not be installed unless you intentionally want the heavier ML stack.

## Environment Variables And Secrets

Set these in the Hugging Face Space **Settings** tab.

Secrets:

```text
GITHUB_TOKEN=your_valid_github_token_here
```

Variables:

```text
GITHUB_API_URL=https://api.github.com/graphql
GITHUB_REST_API_URL=https://api.github.com
GITHUB_PUBLIC_REPO_LIMIT=20
GITHUB_FETCH_COMMIT_COUNTS=false
GITHUB_CACHE_TTL_SECONDS=900
APP_HOST=0.0.0.0
APP_PORT=7860
SCORING_BACKEND=heuristic
```

Do not commit `.env` to Hugging Face or GitHub. Use Hugging Face Space secrets for private values.

## Push Code To The Space

From your local repo:

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git push hf main
```

If your app is on another branch, push that branch to `main` on the Space:

```bash
git push hf your-branch:main
```

Hugging Face rebuilds the Space automatically after each push.

## Test The Deployed App

After the Space finishes building:

```text
https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/
```

Health check:

```text
https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/health
```

Analyze request:

```bash
curl -X POST https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/analyze \
  -H "Content-Type: application/json" \
  -d '{"username":"octocat"}'
```

Expected response includes:

```json
{
  "username": "octocat",
  "rating_score": 72,
  "public_activity": {
    "public_commits": 18,
    "public_prs_created": 4
  },
  "model_info": {
    "data_source": "graphql"
  }
}
```

## Troubleshooting

### Space stuck on Starting

Check that all three ports match:

- Space README: `app_port: 7860`
- Dockerfile: `EXPOSE 7860`
- Uvicorn command: `--port 7860`

### GitHub API rate limit exceeded

Add a valid `GITHUB_TOKEN` as a Hugging Face Space secret and restart/rebuild the Space.

### Bad credentials

Your `GITHUB_TOKEN` is invalid or expired. Replace it in Space secrets, then restart the Space.

### Module import errors

Make sure `requirements.txt` is installed in the Dockerfile. Do not rely on local virtual environments.

### Heavy image or slow build

Use the lightweight `requirements.txt`. Avoid installing `requirements-ml.txt` unless you actually need `torch`, `transformers`, and `langgraph`.

## React Documentation Website

The React documentation website lives in `website/`.

To deploy it separately:

```bash
cd website
npm install
npm run build
```

Deploy `website/dist/` to a static host such as Hugging Face Static HTML Space, Netlify, Vercel, or GitHub Pages.

If deploying the React docs to a Hugging Face Static HTML Space, configure the Space as Static HTML and upload the built `dist/` contents.
