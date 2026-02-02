import threading
from time import sleep


def task():
    thread_name = threading.current_thread().name
    thread_count = threading.active_count()
    print(
        f"Задача вызвана потоком {thread_name}, всего активных потоков {thread_count}"
    )
    sleep(1)
    print(f"Задача выполнилась потоком {thread_name}")


task()
new_thread = threading.Thread(target=task)
new_thread.start()

print(f"Количество активных потоков {threading.active_count()}")
print("END MAIN")
