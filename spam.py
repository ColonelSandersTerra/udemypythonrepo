menu = [
    ["egg", "bacon"],
    ["egg", "sausage", "bacon"],
    ["egg", "spam"],
    ["egg", "spam", "spam", "bacon"],
]

for meal in menu:
    for index in range(len(meal) -1, -1, -1):
            if meal[index] == "spam":
                meal.remove("spam")

print(menu)

