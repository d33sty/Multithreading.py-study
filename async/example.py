import asyncio
import time


async def my_coroutine_1():
    print("my_coroutine_1 start")
    await asyncio.sleep(1)
    print("my_coroutine_1 end")


async def my_coroutine_2():
    print("my_coroutine_2 start")
    await asyncio.sleep(1)
    print("my_coroutine_2 end")


async def main():
    my_task_1 = asyncio.create_task(my_coroutine_1())
    my_task_2 = asyncio.create_task(my_coroutine_2())
    await my_task_1
    await my_task_2


if __name__ == "__main__":
    start_time = time.perf_counter()
    asyncio.run(main())
    print(f"All done in {time.perf_counter() - start_time:.2f}")
