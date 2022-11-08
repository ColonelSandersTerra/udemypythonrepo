answer = 5

print("Please guess number between 1 and 10: ")
guess = int(input())

if  guess < answer:
    print("Please guess higher")
    guess = int(input())
    if guess == answer:
        print("Well come, you guessed it")
elif guess > answer:
    print("please guess lower")
else:
    print("You got it first time.")

