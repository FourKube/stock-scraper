import tweepy as tw
import config
import sys
import numpy as np
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import datetime
import csv

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
	for i in range(len(dateSoup)):
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
		avgSentListStocks.append(avgSent)
	return avgSentListStocks




stockList = ['aapl','cof','born']

print(headlineSentList(stockList,4))
