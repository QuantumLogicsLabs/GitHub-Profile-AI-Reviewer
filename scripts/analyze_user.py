from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.service import AnalyzerService


async def run(username: str) -> None:
    service = AnalyzerService()
    result = await service.analyze(username)
    print(json.dumps(result.model_dump(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub Profile AI Reviewer CLI")
    parser.add_argument("--username", required=True, help="GitHub username")
    args = parser.parse_args()
    asyncio.run(run(args.username))


if __name__ == "__main__":
    main()
