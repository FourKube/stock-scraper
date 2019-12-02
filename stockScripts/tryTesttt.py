import json

with open("theStockSpot.json") as theValue:
	print(theValue)
	file = json.load(theValue)
print(file)
spot = file['currentPlace']
print(spot)
newSpot = spot + 1
file['currentPlace'] = newSpot
print(newSpot)

with open("theStockSpot.json", "w") as aboutToWrite:
	json.dump(file, aboutToWrite)