from concurrent.futures import ThreadPoolExecutor
import time
import threading as t

fn = open("test.txt", "w", encoding="utf-8")


def f1():
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < 0.01:

        print("111", file=fn)


def f2():
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < 0.01:
        print("222", file=fn)


def f3():
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < 0.01:
        print("333", file=fn)


funcs = [f1, f2, f3]

thrs = [t.Thread(target=f) for f in funcs]
for thr in thrs:
    thr.start()

for thr in thrs:
    thr.join()

fn.close()
