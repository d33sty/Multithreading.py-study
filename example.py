from concurrent import interpreters
import time


def consumer(queue_n, queue_r):
    def check_prime(number: int) -> bool:
        """Возвращает True, если переданное число number является простым числом"""
        d = 2
        while number % d != 0:
            d += 1
        return d == number

    while True:
        n = queue_n.get()
        if n is None:
            queue_n.put(None)
            break
        queue_r.put_nowait((n, check_prime(n)))
        print("\tпроверил число", n)


numbers = [
    2985001,
    2985953,
    2986129,
    4465009,
    4469923,
    4469951,
    446998,
    5885449,
    5889887,
    6985367,
    6989657,
    7648939,
    7649801,
    7648411,
    8335571,
    8336599,
    8339987,
    9977581,
    9978131,
    9978607,
    11981707,
    11981707,
    11982721,
    11984429,
    13965059,
    13966783,
    13969859,
    13969897,
    15380003,
    15381101,
    15382901,
    15383477,
    15383923,
    15384293,
    15384973,
    16380000,
    15381102,
    15392906,
    19383488,
    15383924,
    17384294,
    16384900,
]


def main():
    queue_number = interpreters.create_queue()
    queue_results = interpreters.create_queue()
    interps = [interpreters.create() for _ in range(8)]
    threads = [
        interp.call_in_thread(consumer, queue_number, queue_results)
        for interp in interps
    ]
    for number in numbers:
        queue_number.put_nowait(number)
    queue_number.put_nowait(None)
    for thread in threads:
        thread.join()
    while not queue_results.empty():
        number, is_prime = queue_results.get_nowait()
        print(f"\tЧисло {number} {'' if is_prime else 'не'} является простым.")


if __name__ == "__main__":
    start_time = time.perf_counter()
    main()
    print(f"Программа выполнилась за {time.perf_counter()-start_time:.3f}c.")
