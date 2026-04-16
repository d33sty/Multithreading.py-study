import asyncio
from typing import AsyncGenerator


async def get_ticker(file: str) -> AsyncGenerator[str, None]:
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            ticker = line.strip()
            await asyncio.sleep(0)
            yield ticker
