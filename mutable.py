shopping_list = ["milk", "pasta", "egs", "spam", "bread", "rice"]

another_list = shopping_list
print(id(shopping_list))
print(id(another_list))

shopping_list +=["cookies"]
print(shopping_list)
print(id(shopping_list))
print(another_list)

#still only one list by binding all these variables to another_list
a = b = c = d = e = f = another_list

print(a)
print("adding cream")
b.append("cream")
print(c)
print(d)