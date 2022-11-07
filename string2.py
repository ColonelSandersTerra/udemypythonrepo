#
#         012345678901234
parrot = "Norwegian Blue"

print(parrot)

print(parrot[3])

print(parrot[0:6]) #Norweg
print(parrot[:9])
print(parrot[10:])
#if no : in brackets, that is an index
print()
print(parrot[-4:-2])
print(parrot[-4:12])

print(parrot[0:6:2])
print(parrot[0:6:3])

number = "9,233:372:036 854,775;807"
print(number[1::4])

seperators = number[1::4]
print(seperators)

values = "".join(char if char not in seperators else " " for char in number).split()
print([int(val) for val in values])


