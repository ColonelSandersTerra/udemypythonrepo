def multiply(x:float, y:float) -> float:
    result = x * y
    return result


def is_palindrome(string: str) -> bool:
    return string[::-1].casefold() == string.casefold()


def is_palindrome_sentence(sentence):
    string = ""
    for char in sentence:
        if char.isalnum():
            string += char

    return is_palindrome(string)


# sentence = input("Please enter a word to check: ")
# if is_palindrome_sentence(sentence):
#     print("'{}' is a palindrome".format(sentence))
# answer = multiply(18,3)
# print(answer)

def fibonacci(n):
    """Return the 'n'th Fibonacci number, for positive 'n'."""
    if 0 <= n <= 1:
        return n
    
    n_minus1, n_minus2 = 1, 0

    result = None
    for f in range(n -1):
        result = n_minus2 + n_minus1
        n_minus2 = n_minus1
        n_minus1 = result
    
    return result

for i in range(100):
    print(i, fibonacci(i))