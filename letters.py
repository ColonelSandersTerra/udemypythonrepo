letters = "abcdefghijklmnopqrstuvwxyz"

backwards = letters[25::-1] #if we are using negative step, and empty end index, it'll default to start of the string
print(backwards)
backwards = letters[::-1] #reversing string idiom
print(backwards)

backwards = letters[:-9:-1]
print(backwards)
print(letters[-1:])
print(letters[:1])

letters = ""
print(letters[-1:]) #no error even if empty string
print (letters[:1]) #no error even if empty string

#print letters