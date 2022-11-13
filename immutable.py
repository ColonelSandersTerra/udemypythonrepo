result = True
another_result = result
print(id(result))
print(id(another_result))

result = False
print(id(result))
print()
print()

result = True
another_result = result

result = False
print(result)
print(another_result)