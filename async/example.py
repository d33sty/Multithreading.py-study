from time import sleep, perf_counter
from itertools import count
from random import randrange


total_count = count(1)


class Fisherman:
    def __init__(self, name: str = ""):
        self.name = name

    def get(self):
        sleep(randrange(1, 11))
        print(f"{self.name} поймал одну, всего {next(total_count)}")


def main():
    f1 = Fisherman("Рыбак")
    #  ???


if __name__ == "__main__":
    start_time = perf_counter()
    main()
    print(f"total time {perf_counter() - start_time}")