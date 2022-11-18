def multiply(x, y):
    result = x * y
    return result


def is_palindrome(string):
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
answer = multiply(18,3)
print(answer)
