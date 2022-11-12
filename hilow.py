low = 1
high = 100

print("Please think of a nunber between {} and {}".format(low, high))
input("Press ENTER to start")

guesses = 1
while low != high:
    guess = low + (high - low) // 2 # effectively round down
    high_low = input("My guess is {}. Should I guess higher or lower?" 
    "Enter h or l, or c if my guess was correct: "
    .format(guess)).casefold()

    if high_low == "h":
        low = guess + 1
    elif high_low == "l":
        high = guess - 1
    elif high_low == "c":
        print("I got it in {} guesses!".format(guesses))
        break
    else:
        print("Please enter h, l or c")

    guesses += 1 #In Python, the variable is evaluated only once instead of twice in guesses = guesses + 1
else:
    print("You thought of the number {}".format(low))
    print("I got it in {} guesses".format(guesses))

