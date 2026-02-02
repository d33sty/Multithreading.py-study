from time import sleep


def user_interface():
    while True:
        sleep(0.2)
        print("-", end="", flush=True)


def task():
    while True:
        sleep(0.61)
        print("*", end="", flush=True)


import threading


# Ваше решение


thr1 = threading.Thread(target=user_interface)
thr2 = threading.Thread(target=task)

thr1.start()
thr2.start()
