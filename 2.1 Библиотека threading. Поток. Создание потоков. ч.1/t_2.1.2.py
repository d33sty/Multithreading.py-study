tasks = []
##########


import threading

# Ваше решение

for task in tasks:
    threading.Thread(target=task).start()
