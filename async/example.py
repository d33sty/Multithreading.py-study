import asyncio
from typing import Any, Coroutine

SOURCES: list[str] = [
    "https://yandex.ru",
    "https://www.bing.com",
    "https://www.google.ru",
    "https://www.yahoo.com",
    "https://mail.ru",
    "https://яndex.ru",
    "https://www.youtube.com",
    "https://www.porshe.de",
    "https://www.whatsapp.com",
    "https://www.baidu.com",
]


async def get_headers(url: str) -> None:
    _, hostname = url.rsplit("//")

    try:
        reader, writer = await asyncio.open_connection(hostname, 443, ssl=True)

        query: str = f"HEAD / HTTP/1.1\r\n" f"Host: {hostname}\r\n" f"\r\n"
        writer.write(query.encode())
        await writer.drain()

        line: bytes = await reader.readline()
        text: str = line.decode().rstrip()
        _, status_code, status_text = text.split()

        print(text)

        writer.close()
        await writer.wait_closed()

        print(f"{url} - {status_code} ({status_text})")
    except Exception as e:
        print(f"{url} - {e}")


async def main():
    tasks: list[Coroutine[Any, Any, None]] = [get_headers(s) for s in SOURCES]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())