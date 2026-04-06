entities = []


import asyncio

# импортируйте необходимое
from typing import Callable
import concurrent.futures


async def main():
    ents = []
    blocking_ents = []
    for e in entities:
        if isinstance(e, Callable):
            blocking_ents.append(e)
        else:
            ents.append(e)

    with concurrent.futures.ThreadPoolExecutor(len(blocking_ents)) as pool:
        loop = asyncio.get_running_loop()
        tasks = [asyncio.create_task(e) for e in ents]
        blocking_tasks = [loop.run_in_executor(pool, e) for e in blocking_ents]
        results = []
        for c in asyncio.as_completed(tasks + blocking_tasks):
            results.append(await c)

        print(results)


if __name__ == "__main__":
    asyncio.run(main())
