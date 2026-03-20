def my_awesome_gen():
    # Ваше решение
    number = 0
    while True:
        received = yield number
        if isinstance(received, int):
            number += received
        elif isinstance(received, float):
            number *= received
        else:
            return "Ошибка: введите число типа int или float"


g = my_awesome_gen()

print(g.send(None))  # Выводит 0
print(g.send(10))  # Выводит 10
print(g.send(11))  # Выводит 21
print(g.send(0.5))  # Выводит 10.5
print(g.send(100))  # Выводит 110.5
print(
    g.send("ok")
)  # Возбуждается ошибка StopIteration: Ошибка: введите число типа int или float
