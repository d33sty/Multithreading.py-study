import threading
from time import sleep

result = "*"


def test(time_sleep: float | int = 0):
    global result
    sleep(time_sleep)
    result += "--*!"


test()
thr_1 = threading.Thread(target=test, args=(1,))
thr_1.start()
thr_2 = threading.Thread(target=test, args=(2,))
thr_2.start()
thr_2.join()  # <- ожидание завершения второго потока

print(result)

# *--*!--*!--*!

# *--*!
