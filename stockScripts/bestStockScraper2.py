'''
second generation of stock scraper. Old name was fin2.py
Fixed some bugs from the first generation, as well as now includes
sentiment analysis from twitter tickers and company name
as well as sentiment analysis from news articles headlines


'''

#tweepyNumpyNltkRequestsPandasBS4
import json
import tweepy as tw
import config
import sys
import numpy as np #lamda needs
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA #lambda needs
import os
import requests #lambda needs
import pandas as pd #lamda needs
from bs4 import BeautifulSoup #labmda needs
import datetime
import csv
from scrapeHelper import combineAllPages, getTmRanks, combineValPages, combineFinPages, combineOwnPages, combinePerfPages, combineTechPages, getResults, combinePredictorsAndResultsToCSV, ultimateCSV


####################################################################
####################################################################
##################  HEADLINE SENTIMENT VALUES  #####################
####################################################################
####################################################################
'''
Returns a list of all of the news articles on this page 
and the soup
Args: ticker in a string type
Returns: article list, soup
'''
def getAllArticles(ticker):
	allArticles = []
	page = 'https://finviz.com/quote.ashx?t=' + ticker
	r = requests.get(page)
	soup = BeautifulSoup(r.content, "html.parser")
	articleSoup = soup.find_all("a", {"class": "tab-link-news"}) #gets you link to news headlines
	for i in range(len(articleSoup)):
		anArticle = articleSoup[i].text
		allArticles.append(anArticle)
	return allArticles, soup

'''
Returns the articles within the given number of days
Args: ticker in string type, and number of days to go back to get articles
Returns: only those articles within the date
'''
def getArticlesWithinDate(ticker, numDays):
	allArticles, soup = getAllArticles(ticker)
	monthList = ["Jan","Feb","Mar","Apr","May","Jun",
	"Jul","Aug","Sep","Nov","Dec"]
	articlesWithinDate = []
	numOfArticlesToInclude = 0
	dateSoup = soup.find_all("td", {"align": "right"}) #gets you date
	for i in range(len(allArticles)):
		firstThreeChar = dateSoup[i].text[0:3]
		if (firstThreeChar in monthList):
			originalDate = dateSoup[i].text[0:9]
			checkedDate = checkDate(originalDate, numDays)
			if (checkedDate):
				numOfArticlesToInclude += 1
			else:
				break
		else:
			numOfArticlesToInclude += 1
	#if allArticles is empty
	if (len(allArticles) == 0):
		return None
	for i in range(numOfArticlesToInclude):
		articlesWithinDate.append(allArticles[i])
	return articlesWithinDate

'''
This function will convert a date from the finviz website to datetime
arg: string article date in form "Jun-20-19"
returns: datetime date
'''
def checkTimeHelper(date):
    newDate = date.split('-')
    monthStr = newDate[0]
    monthDic = {
    	"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    	"May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    	"Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }
    monthNum = monthDic[monthStr]
    day = int(newDate[1])
    year = int("20" + str(newDate[2]))
    datetimeDate = datetime.datetime(year,monthNum,day)
    return datetimeDate

'''
This function will check if Time is within range
Args: string article date in form "Jun-20-19"
Returns: True if in range, False if out of range
'''
def checkDate(articleDate, numDays):
    convertedArticleDate = checkTimeHelper(articleDate)
    today = datetime.datetime.now()
    d = datetime.timedelta(days = numDays)
    cutOffDate = today - d
    if cutOffDate <= convertedArticleDate:
        return True
    else:
        return False

'''
This function will take a list of strings and return a list of matching polarity score
arg: list of strings
returns: list of polarity scores
'''
def listToSentiment(theList):
    sia = SIA()
    sentimentList = []
    for i in range(len(theList)):
        pol_score = sia.polarity_scores(theList[i])
        sentimentList.append(pol_score["compound"])
    return sentimentList

'''
This function will give the average sentiment of headlines for a period of time
arg: ticker and numDays
returns: average sentiment value
'''
def getHeadlineSentForStock(ticker, numDays):
    articlesWithinDate = getArticlesWithinDate(ticker,numDays)
    #handle situation where there are no articles
    if (articlesWithinDate == None):
    	return None
    headlineSent = listToSentiment(articlesWithinDate)
    total = 0
    for i in range(len(headlineSent)):
        total = total + headlineSent[i]
    if (total==0): #here to catch a division by 0 error
    	return 0
    finalSentValue = total/len(headlineSent)
    return finalSentValue

'''
This function will return the list of average sentiment values for stocklist
arg: stock list and numDays
returns: list of average sentiment for stocklist
'''
def headlineSentList(stockList, numDays):
	avgSentListStocks = []
	for i in range(len(stockList)):
		avgSent = getHeadlineSentForStock(stockList[i],numDays)
		if (avgSent == 0):
			avgSentListStocks.append(None)
		else:
			avgSentListStocks.append(avgSent)
	return avgSentListStocks



####################################################################
####################################################################
################  7-DAY TWITTER SENTIMENT VALUES  ##################
####################################################################
####################################################################
'''
Returns polarity score of a single tweet
'''
def getSingleSent(tweet):
	sia = SIA()
	pol_score = sia.polarity_scores(tweet)
	score = pol_score["compound"]
	return score   
'''
gets all tweets with keyword for the last 7 days
args: keyword and number of tweets
return: average sentiment
'''
def twitterSentiment(keyword, numTweets):
	# OAuth process, using the keys and tokens
	auth = tw.OAuthHandler(config.consumer_key, config.consumer_secret)
	auth.set_access_token(config.access_key, config.access_secret)
	# Creation of the actual interface, using authentication
	api = tw.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
	search_words = str(keyword)
	date_since = "2008-6-8"

	tweets = tw.Cursor(api.search,
				  q=search_words,
				  lang="en",
				  since=date_since).items(numTweets) #100 items
	tweets
	tweetList = []
	sentList = []
	for tweet in tweets:
		tweetList.append(tweet.text)
		sentList.append(getSingleSent(tweet.text))
	total = 0
	for i in range(len(sentList)):
		total = total + sentList[i]
	if total != 0:
		avgSentiment = total/len(sentList)
	else:
		avgSentiment = 0
	return avgSentiment

'''
This function will return the list of average sentiment values for stocklist
arg: stock list
returns: list of average sentiment for stocklist
'''
def twitterSentList(stockList):
	avgSentListStocks = []
	for i in range(len(stockList)):
		avgSent = twitterSentiment(stockList[i],20) #number of stocks
		if (avgSent == 0):
			avgSentListStocks.append(None)
		else:
			avgSentListStocks.append(avgSent)
	return avgSentListStocks

####################################################################
####################################################################
################  GET THE QUARTER (Q1,Q2,Q3,Q4)  ###################
####################################################################
####################################################################
'''
adds a column of what quarter it is
'''
def whatQuarterIsIt():
	mydate = datetime.datetime.now()
	myMonth = mydate.strftime("%B")
	if (myMonth == "January" or myMonth=="February" or myMonth=="March"):
		QT = 1
	elif (myMonth == "April" or myMonth=="May" or myMonth=="June"):
		QT = 2
	elif (myMonth == "July" or myMonth=="August" or myMonth=="September"):
		QT = 3
	elif (myMonth == "October" or myMonth=="November" or myMonth=="December"):
		QT = 4
	else:
		print("theres an error in the months...")
		QT = -1
	return QT


####################################################################
####################################################################
############  FUNCTIONS FOR COMBINING ALL PREDICTORS  ##############
####################################################################
####################################################################

'''
This method combines all predictors to one dataframe
Creates a CSV with todays date "-AllPredictors"
Returns Dataframe
'''
def combineAllpredictors():
	#original (overview dataframe) # rankings
	print("Webscaping data...")
	rankingsDF = getTmRanks()
	#other tabs dataframes
	print("All Rankings Complete: 1/8")
	valDF = combineValPages()
	print("Valuation Complete: 2/8")
	finDF = combineFinPages()
	print("Financial Complete: 3/8")
	ownDF = combineOwnPages()
	print("Ownership Complete: 4/8")
	perfDF = combinePerfPages()
	print("Performance Complete: 5/8")
	techDF = combineTechPages()
	print("Technical Complete: 6/8")

	# News sentiment values
	stockList = rankingsDF['Stock Name'].tolist()
	avgSentListQuarter = headlineSentList(stockList,90)
	avgSentListMonth = headlineSentList(stockList,30)
	avgSentListWeek = headlineSentList(stockList,7)
	dfNewsSent = pd.DataFrame(avgSentListWeek, columns=["Week's Headline Sentiment"])
	dfNewsSent["Month's Headline Sentiment"] = avgSentListMonth
	dfNewsSent["Quarter's Headline Sentiment"] = avgSentListQuarter
	print("Finviz News Sentiment Complete: 7/8")

	# Twitter sentiment values
	companyNameList = rankingsDF['Company'].tolist()
	twitterTickerSentimentList = twitterSentList(stockList)
	twitterCompanySentimentList = twitterSentList(companyNameList)
	dfTwitterSent = pd.DataFrame(twitterTickerSentimentList, columns=["Ticker Twitter Sentiment"])
	dfTwitterSent['Company Name Twitter Sentiment'] = twitterCompanySentimentList
	print("Twitter Sentiment Complete: 8/8")

	#add what quarter it is
	rankingsDF["QT"] = whatQuarterIsIt()

	#concatenate all the data frames and remove dublicated columns
	result = pd.concat([rankingsDF, dfNewsSent,dfTwitterSent,valDF,finDF,ownDF,perfDF,techDF], axis=1, join='inner')
	result = result.loc[:,~result.columns.duplicated()] #drops duplicated columns
	len(result.columns)

	#get column names
	mydate = datetime.datetime.now()
	myMonth = mydate.strftime("%B")
	myDay = datetime.datetime.today().day
	colNames = list(result.columns.values)
	result = result[['Stock Name', 'Date','QT','Stock Count', 'Sector', 'Market Cap',"Ticker Twitter Sentiment",
	"Company Name Twitter Sentiment","Week's Headline Sentiment","Month's Headline Sentiment","Quarter's Headline Sentiment",
	'Zacks Ranks','Yahoo Ranks', 'The Street Ranks','Investor Place','Company', 'Industry','Country', 'P/E', 'Price', 'Volume',
	'EPS Time','EPS next 5Y', 'EPS next Y','EPS past 5Y', 'EPS this Y', 'Fwd P/E', 'P/B', 'P/C', 'P/FCF', 'P/S', 'PEG',
	'Sales past 5Y','Curr R', 'Debt/Eq','Divident', 'Earnings', 'Gross M', 'LTDebt/Eq', 'Oper M', 'Profit M','Quick R', 'ROA',
	'ROE', 'ROI', 'Avg Volume','Float', 'Float Short', 'Insider Own','Insider Trans', 'Inst Own', 'Inst Trans', 'Outstanding',
	'Short Ratio','Perf Half','Perf Month', 'Perf Quart', 'Perf Week', 'Perf YTD', 'Perf Year', 'Recom', 'Rel Volume','Volatility M',
	'Volatility W', '52W High', '52W Low', 'ATR', 'Beta', 'Gap', 'RSI','SMA20', 'SMA200', 'SMA50', 'from Open']]
	result.to_csv(str(myMonth) + str(myDay) + '-' + str(mydate.year-2000) + '-' + 'AllPredictors2.csv', index=False)
	return result


####################################################################
####################################################################
########################  COMBINE EVERYTHING  ######################
####################################################################
####################################################################

'''
 This function will combine "-AllPredictors" of previous day and results of today
 Creates new CSV dated today (results day)
'''
def combinePredictorsAndResultsToCSV():
	mydate = datetime.datetime.now()
	myMonth = mydate.strftime("%B")
	myDay = datetime.datetime.today().day
	both = myMonth + str(myDay)
	df1 = pd.read_csv(str(myMonth) + str(myDay-1) + '-' + str(mydate.year-2000) + '-' + 'AllPredictors2.csv')
	df2 = pd.read_csv(str(myMonth) + str(myDay) + '-' + str(mydate.year-2000) + '-' + 'Results.csv')
	df1List = df1['Stock Name'].tolist()
	df2List = df2['Stock Name'].tolist()
	df1 = df1.set_index('Stock Name')
	df2 = df2.set_index('Stock Name')
	doesNotMatch = []
	for i in range(len(df1List)): #grab tickers that df1 has that df2 does not
		if (df1List[i] not in df2List):
			doesNotMatch.append(df1List[i])
	for i in range(len(df2List)): #grab tickers that df1 has that df2 does not
		if (df2List[i] not in df1List):
			doesNotMatch.append(df2List[i])
	
	for i in range(len(doesNotMatch)):
		try:
			df1=df1.drop(doesNotMatch[i])
		except:
			pass
		try:
			df2=df2.drop(doesNotMatch[i])
		except:
			pass
	try:
		df1 = df1.drop('TRUE')
	except:
		pass

	df1['Stock Count'] = df2['Change']
	df1 = df1.rename({'Stock Count': 'Change'}, axis=1)
	df1 = df1.reset_index(level=0)
	#df1.to_csv("sData1.csv", index=False)
	return df1

'''
 This function will combine two complete CSVs into the Ultimate EPS
'''
def ultimateCSV():
	mydate = datetime.datetime.now()
	myMonth = mydate.strftime("%B")
	myDay = datetime.datetime.today().day
	with open("theStockSpot.json") as theValue:
		file = json.load(theValue)
	spot = file['currentPlace']
	df1 = pd.read_csv('sData' + str(spot) + '.csv')
	df2 = combinePredictorsAndResultsToCSV()
	frames = [df1,df2]
	newDF = pd.concat(frames)
	newSpot = spot + 1
	file['currentPlace'] = newSpot
	with open("theStockSpot.json", "w") as aboutToWrite:
		json.dump(file, aboutToWrite)
	#newDF = newDF.drop_duplicates()
	newDF.to_csv('sData'+ str(newSpot) +'.csv', index=False)



####################################################################
####################################################################
##########################  RUN FUNCTIONS  #########################
####################################################################
####################################################################

print('')
print('________________________')
print('Hello, Welcome to DF Stock Webscraper-2. Choose from list below:')
print("Type 'data': to get all predictors(including Sentiment) for tomorrow's EPSs")
print("Type 'result': to get results for today's EPSs")
print("Type 'add': to update the final document")
print("Type: 'd': to be done")
print("Note: If Monday only type 'data', if Friday only type 'result'")

loop = True
while(loop):
	theInput = input('Enter: ')
	if (theInput=="data"):
		now = datetime.datetime.now()
		print("Starting time: " + str(now.hour) + ":" + str(now.minute) + ":" + str(now.second))
		combineAllpredictors()
		print("Data FINISHED (gathered all predictors for tomorrow's EPS)")
		now = datetime.datetime.now()
		print("Ending time: " + str(now.hour) + ":" + str(now.minute) + ":" + str(now.second))
		os.system("say 'ryan. your script is finished executing'")
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
	

