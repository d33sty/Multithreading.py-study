import asyncio
import multiprocessing
import random
import time


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    client_addr = writer.get_extra_info('peername')
    client_name = str(client_addr)
    print(f"[Server] Client {client_addr} connected")
    
    try:
        while True:
            start_time = time.perf_counter()
            
            data = await reader.read(1024)
            if not data:
                break
                
            decoded_data = data.decode().strip()
            
            parts = decoded_data.split(": ")
            if len(parts) >= 2:
                client_name = parts[0]
                numbers_str = parts[1]
            else:
                numbers_str = parts[0]
            
            print(f"[Server] Received from {client_name}: {numbers_str}")
            
            numbers = list(map(int, numbers_str.split()))
            response = str(sum(numbers))
            
            writer.write(response.encode())
            await writer.drain()
            
            elapsed = (time.perf_counter() - start_time) * 1000
            print(f"[Server] Sent '{response}' to {client_name} (took {elapsed:.2f} ms)")
            
    except Exception:
        pass
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"[Server] Connection with {client_name} closed")


async def server_coro(handler, address):
    server = await asyncio.start_server(handler, *address)
    addr = server.sockets[0].getsockname()
    print(f"[Server] Listening on {addr}")
    
    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            print("[Server] Shutting down...")
            server.close()
            await server.wait_closed()
            raise


async def client_coro(address, client_id):
    reader, writer = await asyncio.open_connection(*address)
    client_name = f"Client-{client_id}"
    print(f"[{client_name}] Connected to server")
    
    try:
        for i in range(1000):
            numbers = [random.randint(1, 10) for _ in range(5)]
            msg = f"{client_name}: {' '.join(map(str, numbers))}"
            writer.write(msg.encode())
            await writer.drain()
            print(f"[{client_name}] Sent: {msg}")
            
            data = await reader.read(1024)
            print(f"[{client_name}] Received sum: {data.decode()}")
            
            if i % 100 == 0:
                await asyncio.sleep(0.01)
                
    except Exception:
        pass
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"[{client_name}] Connection closed")


def server_process_target_func(handler, address):
    try:
        asyncio.run(server_coro(handler, address))
    except KeyboardInterrupt:
        print("[Server process] Interrupted")


def client_process_target_func(address, client_id):
    try:
        asyncio.run(client_coro(address, client_id))
    except KeyboardInterrupt:
        print(f"[Client process {client_id}] Interrupted")


if __name__ == "__main__":
    address = ("localhost", 5555)
    
    server_pr = multiprocessing.Process(
        target=server_process_target_func, 
        args=(handler, address)
    )
    server_pr.start()
    
    time.sleep(0.5)
    
    client_prs = []
    for i in range(5):
        pr = multiprocessing.Process(
            target=client_process_target_func, 
            args=(address, i + 1)
        )
        client_prs.append(pr)
        pr.start()
    
    for pr in client_prs:
        pr.join(timeout=30)
        if pr.is_alive():
            pr.terminate()
            pr.join()
    
    print("\n[Main] All clients finished")
    
    server_pr.terminate()
    server_pr.join()
    print("[Main] Server terminated")
    print("[Main] Program finished")