def factorial(n: int) -> int:
    result = 1
    if n <= 1:
        return result
    for i in range(1, n + 1):
        result *= i
    return result

for i in range(1,36):
    print(i, factorial(i))