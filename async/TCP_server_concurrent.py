"""
Пример многопоточного TCP-сервера с параллельной обработкой клиентов.

Этот код демонстрирует:
- Создание сервера в отдельном процессе
- Создание клиентов в отдельных процессах
- Параллельную обработку нескольких клиентов в отедльных потоках

Сервер принимает от клиентов строку с числами, разделенными пробелами,
вычисляет их сумму и возвращает результат в виде: "a+b+c=sum".
"""

import socket
from typing import Tuple
from multiprocessing import Process
import threading
from time import sleep, perf_counter
from random import uniform


def client(address: Tuple[str, int], msg: str) -> None:
    """
    Функция клиента.

    Клиент подключается к серверу, имитирует случайную задержку (2-5 секунд),
    отправляет сообщение и ожидает ответа.
    """
    client_sock = socket.socket()
    client_sock.connect(address)

    # Симуляция различного времени старта клиентов
    t = uniform(2, 5)
    print(f"[Client-{client_sock.getsockname()}] Sleeping for {t:.2f}s")
    sleep(t)

    # Отправка данных
    client_sock.send(msg.encode())

    # Получение и вывод ответа
    response = client_sock.recv(1024).decode()
    print(f"[Client-{client_sock.getsockname()}] Received data: {response}")

    client_sock.close()


def data_processing(conn: socket.socket, addr: Tuple[str, int]) -> None:
    """
    Обработчик данных для конкретного клиента.
    Запускается в отдельном потоке для каждого подключения.
    """
    while True:
        try:
            data = conn.recv(1024)
        except (ConnectionResetError, ConnectionAbortedError):
            # Клиент разорвал соединение
            print(f"[Server] Client-{addr} disconnected")
            break

        if not data:
            # Клиент штатно закрыл соединение
            print(f"[Server] Client-{addr} disconnected")
            break

        print(f"[Server] Received data from {addr}: {data}")

        try:
            # Преобразуем полученные байты в список целых чисел
            numbers = [int(n) for n in data.decode().split()]
            result = sum(numbers)
            msg = f'{"+".join(map(str, numbers))}={result}'
        except Exception as error:
            # В случае ошибки возвращаем её
            msg = repr(error)
        finally:
            conn.send(msg.encode())

    conn.close()


def server(server_sock: socket.socket) -> None:
    """
    Функция сервера.
    Запускается в отдельном процессе, принимает подключения
    и создает для каждого клиента отдельный поток-обработчик.
    """
    address = ("localhost", 5555)

    # Позволяем переиспользовать адрес после завершения сервера
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(address)
    server_sock.listen()

    print(f"[Server] Listening on {address}")

    while True:
        # Блокируемся до подключения нового клиента
        conn, addr = server_sock.accept()
        print(f"[Server] Connection from {addr}")

        # Запускаем обработку клиента в отдельном потоке
        # Это позволяет серверу одновременно обслуживать несколько клиентов
        handler_thread = threading.Thread(target=data_processing, args=(conn, addr))
        handler_thread.start()


if __name__ == "__main__":
    # Создаем и запускаем сервер в отдельном процессе
    server_sock = socket.socket()
    server_process = Process(target=server, args=(server_sock,))
    server_process.start()
    print("[Main] Server process started")

    # Создаем и запускаем 5 клиентов в отдельных процессах
    # Каждый клиент отправляет строку с числами, где последняя цифра - номер клиента
    client_processes = []
    for i in range(5):
        client_msg = f"11 345 23 11902 23{i}"  # 23{i} делает строки уникальными
        client_process = Process(target=client, args=(("localhost", 5555), client_msg))
        client_process.start()
        client_processes.append(client_process)
    print("[Main] All client processes started")

    # Засекаем время для контроля таймаута
    start_time = perf_counter()
    timeout = 8

    # Ожидаем завершения всех клиентских процессов
    for client_process in client_processes:
        client_process.join()

    elapsed = perf_counter() - start_time
    print(f"[Main] Time elapsed: {elapsed:.2f} seconds")

    # Ожидаем завершения сервера с ограничением по времени
    # Оставшееся время: timeout - уже прошедшее время
    remaining_time = max(0, timeout - elapsed)
    server_process.join(remaining_time)

    # Принудительно завершаем процесс сервера,
    # т.к. он в бесконечном цикле ожидания подключений
    if server_process.is_alive():
        print("[Main] Terminating server process")
        server_process.terminate()
        server_process.join()
        server_process.close()

    print("[Main] Program finished")
