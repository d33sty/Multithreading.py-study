import asyncio
import multiprocessing

async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    data = await reader.read(1024)  # читаем данные (в байтах), ограничивая посылку в 1Кб
    print(f"[Server] Received: {data.decode()}")  # декодируем байты

    writer.write(data)  # отправляем данные обратно
    await writer.drain()  # дожидаемся отправки данных
    print("[Server] Sent message back.")

    writer.close()
    await writer.wait_closed()

async def server_coro(handler, address):
    server = await asyncio.start_server(handler, *address)
    async with server:
        await server.serve_forever()


async def client_coro(address):
    msg = "mock_msg"
    reader, writer = await asyncio.open_connection(*address)
    writer.write(msg.encode())
    await writer.drain()
    print("[Client] Message sent.")

    data = await reader.read(1024)
    print(f"[Client] Received: {data.decode()}.")
    writer.close()
    await writer.wait_closed()
    print("[Client] Connection closed.")

def server_process_target_func(handler, address):
    asyncio.run(server_coro(handler, address))

def client_process_target_func(address):
    asyncio.run(client_coro(address))


if __name__ == "__main__":
    address = ("localhost", 5555)
    server_pr = multiprocessing.Process(target=server_process_target_func, args=(handler, address))
    client_pr = multiprocessing.Process(target=client_process_target_func, args=(address,))

    server_pr.start()
    client_pr.start()

    server_pr.join()
    client_pr.join()