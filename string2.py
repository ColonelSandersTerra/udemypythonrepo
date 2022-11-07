#
#         012345678901234
parrot = "Norwegian Blue"

print(parrot)

print(parrot[3])

for i in range(0,14):
    if i % 2 == 0:
        print(parrot[i])

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