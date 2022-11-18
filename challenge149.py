#challenge149.py

def sum_eo(x, y):
    result = 0
    for i in range(1, x):
        if y == 'e':
            if i % 2 == 0:
                result += i
        elif y == 'o':
            if i % 2 == 1:
                result += i
    return result


test = sum_eo(10,'o')
print(test)