import socket


def server() -> None:
    server_sock = socket.socket()
    address = ("localhost", 5555)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(address)
    server_sock.listen()
    while True:
        conn, addr = server_sock.accept()
        print(f"Connection from {addr}")
        while data := conn.recv(1024):
            print(f"received data {data}")
            try:
                numbers = [int(n) for n in data.decode().split()]
                res = sum(numbers)
            except Exception as er:
                msg = repr(er)
            else:
                msg = f'{"+".join(map(str, numbers))}={res}'
            finally:
                conn.send(msg.encode())


if __name__ == "__main__":
    server()
