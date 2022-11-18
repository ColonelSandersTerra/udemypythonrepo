pangram = "The quick brown fox jumps over the lazy dog"

letters = sorted(pangram)
print(letters)

numbers = [2.3, 4.5, 8.7, 3.1, 9.2, 1.6]
sorted_numbers = sorted(numbers) #numbers list order unchanged, numbers.sort would sort in place
print(sorted_numbers)
print(numbers)

another_sorted_numbers = numbers
another_sorted_numbers.sort()
print(numbers)
print(another_sorted_numbers)

missing_letter = sorted("The quick brown fox jumped over the lazy dog",
                        key=str.casefold)
print(missing_letter)

names = ["Graham", "John", "terry", "eric", "Terry", "Michael"]
names.sort(key=str.casefold)
print(names)