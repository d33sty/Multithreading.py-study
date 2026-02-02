import threading
from time import sleep, perf_counter

result = "*"


def test(time_sleep: float | int = 0, s: str = "*"):
    global result
    sleep(time_sleep)
    result += f"--{s}!"


test()
thr_1 = threading.Thread(target=test, args=(1, "1"))
thr_1.start()
thr_2 = threading.Thread(target=test, args=(3, "2"))
thr_2.start()

start_t = perf_counter()
thr_1.join(1.5)
print(f"1 - {perf_counter() - start_t}")

start_t = perf_counter()
thr_2.join(2.2)
print(f"2 - {perf_counter() - start_t}")


print(result)

#  1 - 1.0002477999660186
#  2 - 2.000215300009586
#  *--*!--1!--2!
