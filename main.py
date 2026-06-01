from __future__ import annotations

import argparse
import asyncio
import json

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
