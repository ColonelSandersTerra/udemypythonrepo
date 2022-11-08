age = 24
print("My age is " +str(age) + " years")
print("My age is {0} years".format(age))

print("There are {0} days in {1}, {2}, {3}, {4}, {5}, {6}, {7}"
    .format(31, "Jan", "Mar", "May", "Jul", "Aug", "Oct", "Dec"))

#Replacement fields don't have to be in order
print("Jan: {2}, Feb: {0}, Mar: {2}".format(28, 30, 31))

