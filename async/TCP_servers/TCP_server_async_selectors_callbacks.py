"""
Асинхронный TCP-сервер с использованием select для мультиплексирования ввода-вывода.

Этот код демонстрирует:
- Неблокирующую обработку нескольких клиентов в одном потоке с помощью select
- Сервер, который может одновременно обслуживать множество клиентов без использования
  многопоточности или многопроцессности
- Эффективную модель событийно-ориентированного программирования

Сервер принимает от клиентов строку с числами, разделенными пробелами,
вычисляет их сумму и возвращает результат в виде: "a+b+c=sum".
"""

import socket
import selectors
from typing import Tuple, List
import multiprocessing
from time import sleep
from random import uniform


def client() -> None:
    """
    Функция клиента.
    Подключается к серверу, имитирует случайную задержку,
    отправляет сообщение и выводит ответ сервера.
    """
    client_sock = socket.socket()
    address = ("localhost", 5555)
    client_sock.connect(address)
    sleep(uniform(2, 5))
    msg = "1 2 3 4 5 6 " + str(multiprocessing.current_process().ident % 20)
    client_sock.send(msg.encode())
    response = client_sock.recv(1024)
    print(f"Response from server: {response.decode()}")
    client_sock.close()


def create_server(address: Tuple[str, int]) -> socket.socket:
    """
    Создает и настраивает серверный сокет.
    """
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(address)
    server_socket.listen()
    return server_socket


def handler(data: bytes) -> bytes:
    """
    Обрабатывает полученные данные: разбирает строку с числами,
    вычисляет сумму и формирует ответ.
    """
    try:
        print(f"received data {data}")
        numbers = [int(n) for n in data.decode().split()]
        res = sum(numbers)
    except Exception as er:
        msg = repr(er)
        return msg.encode()
    else:
        msg = f'{"+".join(map(str, numbers))}={res}'
        return msg.encode()


def accept_conn(server_sock: socket.socket, sel: selectors.BaseSelector) -> None:
    """
    Принимает новое подключение и регистрирует клиентский сокет в селекторе
    для отслеживания готовности к чтению.
    """
    try:
        conn, addr = server_sock.accept()
        print(f"Connection from {addr}")
        sel.register(conn, selectors.EVENT_READ, send_response)
    except socket.error as error:
        print(f"Error accepting connection: {error}")


def send_response(client_sock: socket.socke, *args) -> None:
    """
    Читает данные от клиента, обрабатывает их и отправляет ответ.
    При ошибке сокет закрывается.
    """
    data = client_sock.recv(1024)
    if data:
        response = handler(data)
        client_sock.send(response)


def event_loop(server_socket: socket.socket) -> None:
    """
    Главный событийный цикл сервера.
    Использует selector для мониторинга всех активных сокетов.
    При появлении данных на любом из сокетов вызывает соответствующий обработчик.
    """
    with selectors.DefaultSelector() as sel:
        sel.register(server_socket, selectors.EVENT_READ, accept_conn)

        while True:
            for k, _ in sel.select():
                sock: socket.socket = k.fileobj
                callback = k.data
                try:
                    callback(sock, sel)
                except socket.error as error:
                    print(f"Error receiving data: {error}")
                    sock.close()
                    sel.unregister(sock)


if __name__ == "__main__":
    """
    Основной блок: запуск сервера и клиентов.
    Сервер работает в главном потоке, клиенты запускаются в отдельных процессах.
    """
    address = ("localhost", 5555)
    server_socket = create_server(address)

    client_prs = [multiprocessing.Process(target=client, daemon=True) for _ in range(5)]
    for pr in client_prs:
        pr.start()

    event_loop(server_socket)
