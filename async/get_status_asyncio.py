import asyncio
from time import perf_counter


sources = ["https://yandex.ru",
           "https://www.bing.com",
           "https://www.google.ru",
           "https://www.yahoo.com",
           "https://mail.ru",
           "https://яndex.ru",
           "https://www.youtube.com",
           "https://www.porshe.de",
           "https://www.whatsapp.com",
           "https://www.baidu.com"]

status_stor = {}
sum_ex_time = 0


async def get_status(url: str) -> tuple[str, dict]:
    global sum_ex_time
    start_tmp = perf_counter()
    status = None
    
    try:
        _, hostname = url.rsplit("//")
        reader, writer = await asyncio.open_connection(hostname, 443, ssl=True)
        query = (
            f"HEAD / HTTP/1.1\r\n"
            f"Host: {hostname}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        writer.write(query.encode())
        await writer.drain()
        
        data = await reader.readline()
        writer.close()
        await writer.wait_closed()
        
        if data:
            status = data.decode().strip()
        else:
            status = "No response"
        
    except Exception as err:
        status = f"Error: {repr(err)}"
    
    delta = perf_counter() - start_tmp
    sum_ex_time += delta
    
    print(f"{url} | {status} | {delta:.2f}s")
    return url, status


async def main():
    tasks = [get_status(source) for source in sources]
    results = await asyncio.gather(*tasks)
    for url, status in results:
        status_stor[url] = status


if __name__ == '__main__':
    start_time = perf_counter()
    asyncio.run(main())
    print(f"Выполнено за: {perf_counter() - start_time:.2f}с.")
    print(f"Сумма времени всех запросов: {sum_ex_time:.2f}с.")