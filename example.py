from time import sleep
from threading import Timer, Thread
from typing import Callable

result = False


def task(*args):
    global result
    print("task started")
    sleep(0.5)
    result = True
    print("task ended")


def callback_task():
    print("callback")


def callback_handler(
    task: Callable = None, args=(), callback_task: Callable = None
) -> None:
    # не меняйте значение result
    # дополните код
    global result
    thr = Thread(target=task, args=args, daemon=True)
    thr.start()
    tim = Timer(0.3 + 0.05, callback_task)
    tim.start()
    thr.join(0.3)
    if not result:
        tim.cancel()


callback_handler(task, tuple(), callback_task)
