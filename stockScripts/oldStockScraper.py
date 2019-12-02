'''
The original finfiz stock scraper run functions. Old name was fin.py
'''

from scrapeFinviz import combineAllpredictors, getResults, combinePredictorsAndResultsToCSV, ultimateCSV

print('')
print('________________________')
print('Hello, Welcome to DF Stock Webscraper. Choose from list below:')
print("Type 'data': to get all predictors for tomorrow's EPSs")
print("Type 'result': to get results for today's EPSs")
print("Type 'add': to update the final document")
print("Type: 'd': to be done")
print("Note: If Monday only type 'data', if Friday only type 'result'")

loop = True
while(loop):
	theInput = input('Enter: ')
	if (theInput=="data"):
		combineAllpredictors()
		print("Data FINISHED (gathered all predictors for tomorrow's EPS)")
	elif (theInput=="result"):
		getResults()
		print("Result FINISHED (gathered all results from Today)")
	elif (theInput=="combine"):
		combinePredictorsAndResultsToCSV()
	elif (theInput=="add"):
		ultimateCSV()
		print("Add FINISHED (combined documents successfully)")
	elif (theInput=="d"):
		loop = False
		print("Program Ended. Thanks")
	else:
		print('Sorry that entry is not recognized. Please try again.')
	print('')
	print('________________________')
print('')
