from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from backroom_agent.agent.graph import run_once


def main() -> None:
    load_dotenv()

    text = os.getenv("PROMPT", "Hello from BackroomAgent")
    msg = asyncio.run(run_once(text))
    print(msg.content)


if __name__ == "__main__":
    main()
