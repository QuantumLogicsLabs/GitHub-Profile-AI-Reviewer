# 🤖 GitHub Profile AI Reviewer

<div align="center">

![GitHub Profile AI Reviewer](https://img.shields.io/badge/AI--Powered-GitHub%20Profile%20Reviewer-0D1117?style=for-the-badge&logo=github&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Workflow-4A90E2?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active%20Development-00C853?style=for-the-badge)

**An AI-powered GitHub profile analysis engine that predicts developer level, strongest language, hiring readiness, and consistency score — powered by LangGraph agentic workflows, Hugging Face Transformers, and PyTorch.**

[Features](#-features) • [Architecture](#-architecture) • [Tech Stack](#-tech-stack) • [GraphQL Queries](#-github-graphql-api) • [LangGraph Pipeline](#-langgraph-pipeline) • [Models](#-hugging-face-models) • [Getting Started](#-getting-started)

</div>

---

## 📌 Overview

GitHub Profile AI Reviewer is a **pure AI project** that analyzes any GitHub profile and produces a structured developer assessment report. It goes beyond surface-level stats — using LangGraph agentic workflows, Hugging Face Transformer models, and GitHub's GraphQL API to deeply understand _how_ a developer codes, not just _what_ they've built.

> Designed to integrate seamlessly with the **GitHub Streak Viewer** for a complete developer analytics dashboard.

---

## ✨ Features

| Feature                             | Description                                                                        |
| ----------------------------------- | ---------------------------------------------------------------------------------- |
| 🎯 **Developer Level Prediction**   | Junior / Mid / Senior / Staff classification with confidence score                 |
| 💬 **Strongest Language Detection** | Identified from commit patterns, PR history, and repo metadata via GraphQL         |
| ✅ **Hiring Readiness Score**       | Composite score (0–100) based on activity, documentation, and code quality signals |
| 📈 **Consistency Score**            | Measures contribution regularity, streak patterns, and contribution graph momentum |
| 🧠 **LangGraph Agent Pipeline**     | Multi-step stateful reasoning chain with tool-use and typed state                  |
| 🤗 **HuggingFace Embeddings**       | CodeBERT / StarCoder embeddings for deep code understanding                        |
| 🔥 **PyTorch Scoring Model**        | Custom neural scoring model trained on developer profiles                          |
| 🔗 **Streak Viewer Integration**    | Connects to GitHub Streak Viewer for enhanced temporal analysis                    |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       User Interface                         │
│               (Web App / CLI / REST API)                     │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                  LangGraph Orchestrator                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌─────────┐  │
│  │  Fetch   │→ │ Analyze  │→ │  Embed &    │→ │ Score & │  │
│  │  Node    │  │  Node    │  │  Classify   │  │ Report  │  │
│  └──────────┘  └──────────┘  └─────────────┘  └─────────┘  │
└─────────────────────────┬────────────────────────────────────┘
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
GitHub GraphQL API    HuggingFace +      Streak Viewer
(commits, stars,      PyTorch Models     (consistency)
 PRs, languages,      (CodeBERT, BERT,
 contribution graph)   StarCoder, Qwen)
```

---

## 🧰 Tech Stack

### 🔍 GitHub GraphQL API — _Absolutely Essential_

> The GitHub GraphQL API is the backbone of this project. Every advanced analytics platform uses it heavily. The REST API simply cannot match its depth and flexibility.

**Why GraphQL over REST:**

- Fetch _exactly_ what you need in a single request — no over-fetching
- Access contribution graphs, language breakdowns, PR history, and commit activity all in one query
- Drastically reduces API rate limit consumption
- Enables complex nested queries: repos → commits → authors → languages

**What we use it for:**

| Data                         | Purpose in Project                          |
| ---------------------------- | ------------------------------------------- |
| `contributionsCollection`    | Contribution graph, consistency score       |
| `repositories` + `languages` | Language mastery detection                  |
| `pullRequests`               | Code collaboration signals for hiring score |
| `commitComments` + `issues`  | Community engagement metrics                |
| `starredRepositories`        | Interest graph & domain detection           |
| `pinnedItems`                | Developer self-presentation analysis        |

---

### 🤗 Hugging Face Transformers — _Critical for AI Scoring_

> The essential library for NLP, embeddings, and AI-powered profile analysis. Gives direct access to BERT, CodeBERT, StarCoder, Llama, Qwen, and thousands of pre-trained models.

**What it enables:**

- Deep NLP understanding of READMEs, bios, and commit messages
- Code embeddings that capture semantic meaning, not just syntax
- Local inference — no external API costs

**Models used in this project:**

| Model                                                             | Task                                     | Why                                                   |
| ----------------------------------------------------------------- | ---------------------------------------- | ----------------------------------------------------- |
| **[CodeBERT](https://huggingface.co/microsoft/codebert-base)**    | Code embedding & language classification | Understands code semantics, not just token frequency  |
| **[BERT](https://huggingface.co/bert-base-uncased)**              | README & bio NLP analysis                | Extracts skills and seniority signals from free text  |
| **[StarCoder](https://huggingface.co/bigcode/starcoder)**         | Code quality estimation                  | Trained on 80+ languages sourced directly from GitHub |
| **[Qwen2.5-Coder](https://huggingface.co/Qwen/Qwen2.5-Coder-7B)** | Developer level classification           | State-of-the-art code understanding, runs locally     |

**Usage example:**

```python
from transformers import AutoTokenizer, AutoModel
import torch

# Load CodeBERT for code embeddings
tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
model     = AutoModel.from_pretrained("microsoft/codebert-base")

def embed_code_snippet(code: str) -> torch.Tensor:
    inputs  = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :]  # CLS token embedding
```

---

### 🔥 PyTorch — _Most Important AI Framework for the Future_

> PyTorch is the dominant framework in AI research and production. Mastering it means you can build custom LLMs, AI agents, security models, and compiler AI from scratch.

**Why PyTorch is non-negotiable:**

- Used by Meta, Tesla, OpenAI, Hugging Face — the entire AI research world
- Foundation of every major LLM: LLaMA, Mistral, Falcon, Qwen
- Flexible dynamic computation graph — essential for research and experimentation
- Full control over model architecture, training loop, and inference pipeline

**If you master PyTorch, you can build:**

- Custom LLMs from scratch
- AI agents with learned behavior
- Security anomaly detection models
- Compiler AI and code synthesis systems

**In this project, PyTorch powers the custom scoring model:**

```python
import torch
import torch.nn as nn

class DeveloperScoringModel(nn.Module):
    """
    Custom neural network that takes developer feature vectors
    (from CodeBERT embeddings + GraphQL signals) and outputs:
    developer level, hiring score, and consistency score.
    """
    def __init__(self, input_dim: int = 768):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
        )
        self.level_head        = nn.Linear(128, 4)  # Junior / Mid / Senior / Staff
        self.hiring_score_head = nn.Linear(128, 1)  # 0–100
        self.consistency_head  = nn.Linear(128, 1)  # 0–100

    def forward(self, x: torch.Tensor):
        features       = self.encoder(x)
        level          = self.level_head(features)
        hiring_score   = torch.sigmoid(self.hiring_score_head(features)) * 100
        consistency    = torch.sigmoid(self.consistency_head(features)) * 100
        return level, hiring_score, consistency
```

---

### 🐳 Docker — _Mandatory for AI Engineers_

> Docker is a non-negotiable skill for any future AI engineer. It ensures your models, dependencies, and GPU environment are perfectly reproducible — on any machine, anywhere.

**Why Docker is essential for this project:**

- PyTorch + CUDA versions must be pinned exactly — Docker guarantees this
- HuggingFace model caches are large; Docker volumes manage them cleanly
- Deploy the full stack (API + models + database) with a single command
- The difference between "works on my machine" and a real production deployment

```dockerfile
# Dockerfile
FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download models at build time — no cold start in production
RUN python -c "from transformers import AutoModel; \
               AutoModel.from_pretrained('microsoft/codebert-base')"

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: "3.9"
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
    volumes:
      - hf_cache:/root/.cache/huggingface # Persist downloaded models
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu] # GPU passthrough for PyTorch

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"] # Cache GitHub GraphQL responses

volumes:
  hf_cache:
```

---

### 🔁 LangGraph — _Agentic Workflow Orchestration_

> LangGraph turns the analysis steps into a stateful, inspectable agent graph. Every node is a discrete step with typed state — making the entire pipeline debuggable, extensible, and production-ready.

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProfileState(TypedDict):
    username:            str
    graphql_data:        dict   # Raw data from GitHub GraphQL
    language_embeddings: list   # CodeBERT embeddings per repo
    feature_vector:      list   # Final PyTorch model input
    developer_level:     str
    hiring_score:        float
    consistency_score:   float
    final_report:        str

graph = StateGraph(ProfileState)

graph.add_node("fetch_graphql",       fetch_github_graphql)   # GitHub GraphQL API
graph.add_node("embed_repositories",  embed_with_codebert)    # HuggingFace Transformers
graph.add_node("score_with_pytorch",  run_pytorch_model)      # PyTorch scoring model
graph.add_node("compute_consistency", fetch_streak_viewer)    # Streak Viewer integration
graph.add_node("generate_report",     generate_final_report)  # Structured output

graph.set_entry_point("fetch_graphql")
graph.add_edge("fetch_graphql",       "embed_repositories")
graph.add_edge("embed_repositories",  "score_with_pytorch")
graph.add_edge("score_with_pytorch",  "compute_consistency")
graph.add_edge("compute_consistency", "generate_report")
graph.add_edge("generate_report",     END)

app = graph.compile()
```

---

## 🔍 GitHub GraphQL API

### Core Query — Full Profile Analysis

```graphql
query AnalyzeProfile($username: String!) {
  user(login: $username) {
    name
    bio
    createdAt
    followers {
      totalCount
    }

    # Contribution graph — feeds consistency score
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }

    # Top repositories with full language breakdown
    repositories(first: 20, orderBy: { field: STARGAZERS, direction: DESC }) {
      nodes {
        name
        stargazerCount
        forkCount
        primaryLanguage {
          name
        }
        languages(first: 5) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 1) {
                totalCount # Total commit count per repo
              }
            }
          }
        }
      }
    }

    # Pull request history — collaboration & hiring signal
    pullRequests(first: 50, states: MERGED) {
      totalCount
      nodes {
        repository {
          nameWithOwner
        }
        mergedAt
      }
    }
  }
}
```

---

## 🤗 Hugging Face Models

### Model Selection Guide

```
Use case                              →  Recommended model
─────────────────────────────────────────────────────────────
Embed code snippets                   →  microsoft/codebert-base
Classify programming language         →  huggingface/CodeBERTa-language-id
Analyze README / bio text             →  bert-base-uncased
Estimate code quality / complexity    →  bigcode/starcoder
Developer level classification        →  Qwen/Qwen2.5-Coder-7B
Local inference (low resource)        →  Qwen/Qwen2.5-Coder-1.5B
```

---

## 🗄 Supporting Tools

| Tool                                          | Category      | Purpose                                                     |
| --------------------------------------------- | ------------- | ----------------------------------------------------------- |
| **[FastAPI](https://fastapi.tiangolo.com/)**  | Backend       | Async REST API serving analysis results                     |
| **[Redis](https://redis.io/)**                | Caching       | Cache GraphQL responses to stay within GitHub rate limits   |
| **[LangSmith](https://smith.langchain.com/)** | Observability | Trace every LangGraph node — essential for debugging agents |
| **[Pydantic v2](https://docs.pydantic.dev/)** | Validation    | Typed state models for LangGraph                            |

---

## 📦 Getting Started

### Prerequisites

```
Python 3.11+
GitHub Personal Access Token  (read:user scope)
Docker & Docker Compose
NVIDIA GPU  (optional, but recommended for PyTorch)
```

### Installation

```bash
git clone https://github.com/yourusername/github-profile-ai-reviewer
cd github-profile-ai-reviewer

# Recommended — Docker
cp .env.example .env
# Fill in GITHUB_TOKEN, LANGSMITH_API_KEY
docker-compose up --build

# Or — Local
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run Analysis

```bash
# CLI
python main.py --username gvanrossum

# REST API
curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"username": "gvanrossum"}'
```

### Sample Output

```json
{
  "username": "gvanrossum",
  "developer_level": "Staff / Principal",
  "confidence": 0.97,
  "strongest_language": "Python",
  "language_breakdown": { "Python": 91, "C": 6, "Shell": 3 },
  "hiring_readiness_score": 96,
  "consistency_score": 88,
  "graphql_signals": {
    "total_commits": 4821,
    "merged_prs": 312,
    "total_contributions": 2103
  },
  "streak_data": {
    "current_streak": 21,
    "longest_streak": 365
  },
  "model_info": {
    "embedding_model": "microsoft/codebert-base",
    "scoring_model": "DeveloperScoringModel v1.2.0",
    "embedding_dim": 768
  }
}
```

---

## 🗺 Roadmap

- [x] LangGraph pipeline skeleton
- [x] GitHub GraphQL API integration
- [x] HuggingFace CodeBERT embeddings
- [x] PyTorch custom scoring model
- [x] Docker + docker-compose setup
- [x] Streak Viewer integration
- [ ] Fine-tune scoring model on labeled developer dataset
- [ ] StarCoder-based code quality estimation node
- [ ] Vector similarity search ("find developers like X")
- [ ] Frontend dashboard (React + shadcn/ui)
- [ ] Batch org-level hiring pipeline
- [ ] GitHub Action: auto-review on PR open

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ using **GitHub GraphQL** • **Hugging Face Transformers** • **PyTorch** • **LangGraph** • **Docker**

_Part of the GitHub Developer Analytics Suite — integrates with [GitHub Streak Viewer]_

</div>
