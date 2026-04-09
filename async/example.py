import asyncio


async def main(file):
    process = await asyncio.create_subprocess_exec(
        "python.exe",
        "-c",
        "import time; time.sleep(1);"
        'print("Субпроцесс завершился и напечатал это сообщение.")',
        stdout=file,
    )
    print(process)
    await asyncio.sleep(2)


if __name__ == "__main__":
    with open("new_file", "w") as file:
        asyncio.run(main(file))
