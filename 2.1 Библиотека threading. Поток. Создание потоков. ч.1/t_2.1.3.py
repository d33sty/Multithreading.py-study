tasks = []
args = []

##########


def my_task():
    pass


def my_new_task():
    pass


tasks = [my_task, my_new_task]
for task in tasks:
    print(task.__name__)

import threading

# Ваше решение

for t, a in zip(tasks, args):
    threading.Thread(target=t, args=(a,), name=t.__name__).start()
