#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from graphs.graph import main_graph


async def run_query(question: str) -> dict:
    return await main_graph.ainvoke({"user_question": question})


def main():
    parser = argparse.ArgumentParser(description="AIQuery 本地智能问数")
    parser.add_argument("-q", "--question", default="查询所有商品及其价格")
    parser.add_argument("--server", action="store_true")
    args = parser.parse_args()

    if args.server:
        from main import start_server

        start_server()
        return

    result = asyncio.run(run_query(args.question))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
