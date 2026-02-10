import time
import random


def shutdown():
    print(f"ALL DONE! by {threading.current_thread().name}")


def finalizer():
    print(f"STAGE DONE! by {threading.current_thread().name}")


def task_stage1():
    time.sleep(random.uniform(0, 1))
    print(f"stage #1 done by {threading.current_thread().name}")


def task_stage2():
    time.sleep(random.uniform(0, 1))
    print(f"stage #2 done by {threading.current_thread().name}")




import threading

# Создайте объект барьера
barrier = threading.Barrier(4, finalizer)
# Создайте целевую функцию, выполняющую задачи в два этапа
def target_func(barrier, task_stage1, task_stage2):
        task_stage1()
        barrier.wait()
        task_stage2()
        if barrier.wait() == 0:
             shutdown()

# Создайте и запустите 4 потока c требуемыми именами
threads = [threading.Thread(target=target_func, name=f"Thread #{i + 1}", args=(barrier, task_stage1, task_stage2)) for i in range(4)]
for thr in threads:
    thr.start()