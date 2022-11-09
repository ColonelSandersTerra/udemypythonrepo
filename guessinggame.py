import random

isQuit = False
highest = 10
answer = random.randint(1,highest)
print(answer) #TODO: Remove after testing

print("Please guess number between 1 and {}: ".format(highest))
guess = int(input())

# if  guess < answer:
#     print("Please guess higher")
#     guess = int(input())
#     if guess == answer:
#         print("Well done, you guessed it")
# elif guess > answer:
#     print("please guess lower")
# else:
#     print("You got it first time.")

while guess != answer:
    if guess == 0:
        print("Game has been quit")
        isQuit = True
        break
    elif guess < answer:
        print("Please guess higher.")
    else:
        print("Please guess lower.")
    guess = int(input())

if isQuit == False:
    print("You guessed correctly!")
