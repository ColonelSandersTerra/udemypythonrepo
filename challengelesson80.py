answer = -1

while answer != 0:
    print("Please choose your option from the list below:")
    print("1.\tLearn Python\n2.\tLearn Java\n3.\tGo swimming\n4.\tHave dinner\n5.\tGo to bed\n0.\tExit")

    answer = int(input())
    print("You selected {}".format(answer))
else:
    print("Exited program!")