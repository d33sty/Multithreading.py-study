import threading
import time


def task(func, arg):
    func(arg)
    print("task done!")


threads = []
for i in range(20):
    threads.append(threading.Thread(target=task, args=(time.sleep, 0.1)))

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
