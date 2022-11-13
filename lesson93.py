data = [
    "Andromeda - Shrub",
    "Bellflower - Flower",
    "China Pink - Flower",
    "Daffodil - Flower",
    "Evening Primrose - Flower",
    "French Marigold - Flower",
    "Hydrangea - Shrub",
    "Iris - Flower",
    "Japanese Camellia - Shrub",
    "Lavender - Shrub",
    "Lilac - Shrub",
    "Magnolia - Shrub",
    "Peony - Shrub",
    "Queen Anne's Lace - Flower",
    "Red Hot Poker - Flower",
    "Snapdragon - Flower",
    "Sunflower - Flower",
    "Tiger Lily - Flower",
    "Witch Hazel - Shrub",
]

flowers = []
shrubs = []
name = ""
# write your code here
for i in range(0, len(data)):
    if " - Flower" in data[i]:
        name = data[i]
        name = name[0:len(name)-9]
        flowers.append(name)
    else:
        name = data[i]
        name = name[0:len(name)-8]
        shrubs.append(name)

print(flowers)
print()
print(shrubs)