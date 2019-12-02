'''All of the methods to web-scrape stock information for companies EPSing tomorrow
from various pages of finviz.com. Also gets stock rankings from yahoo, theStreet, 
investorPlace, and zachs. '''

import pandas as pd
import bs4
import requests
import os
import re
from bs4 import BeautifulSoup
import csv
import datetime

'''
This function webscrapes finviz and
Returns a list of stocks EPSing tomorrow
'''
def getListOfTickersToEPS(tmEPS):
	stockList = []
	r = requests.get(tmEPS, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'})
	soup = bs4.BeautifulSoup(r.content, "html.parser")
	search = soup.find_all("div", {"id":"screener-content"})
	for item in search:
		step1=item.find_all("a", {"class": "screener-link-primary"})
	for i in range(len(step1)):
		ticker = step1[i].text
		stockList.append(ticker)
	return stockList

'''
This function webscrapes the stocks info to a continous list
Returns a continous list of further information about the stocks
'''
def getStockInfo(tmEPS):
	infoList = []
	r = requests.get(tmEPS, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'})
	soup = bs4.BeautifulSoup(r.content, "html.parser")
	search = soup.find_all("div", {"id":"screener-content"})
	for item in search:
		step1=item.find_all("td", {"class": "screener-body-table-nw"})
	for item2 in step1:
		step2=item2.find_all("a", {"class": "screener-link"})
		for i in range(len(step2)):
			if (step2[i].text == "-"):
				infoList.append(None)
			else:	
				infoList.append(step2[i].text)
	return infoList

'''
 This function turns the lists of stocks and continuous list of parameters
into a data frame
'''
def infoToDataFrame(stockList, infoList):
	finalList = []
	count = 0
	for i in range(1,len(stockList)+1):
		listOfList = []
		for z in range(10):
			listOfList.append(infoList[count])
			count += 1
		finalList.append(listOfList)
	df = pd.DataFrame(finalList, columns= ['Stock Count','Company',
		'Sector','Industry','Country','Market Cap', 'P/E','Price',
		'Change','Volume'])
	#del df['Stock Count']
	df.insert(loc=0,column="Stock Name",value=stockList)
	return df

'''
 These functions take a page and make a Data frame 
 Returns Data frame
'''
def todayAfterMarketPage(page):
	stockList = getListOfTickersToEPS(page)
	if (len(stockList)==0):
		return pd.DataFrame()
	infoList = getStockInfo(page)
	df = infoToDataFrame(stockList,infoList) 
	df['EPS Time'] = "Today After Market EPS"
	return df
def tomorrowBeforeMarketPage(page):
	stockList = getListOfTickersToEPS(page)
	if (len(stockList)==0):
		return pd.DataFrame()
	infoList = getStockInfo(page)
	df = infoToDataFrame(stockList,infoList) 
	df['EPS Time'] = "Tomorrow Before Market EPS"
	return df
		
'''
 These functions combines dataframes
 Returns final Data frame
'''
def combineAllPages():
	todayAfter1 = 'https://finviz.com/screener.ashx?v=111&f=earningsdate_todayafter&ft=4'
	tmBefore1 = 'https://finviz.com/screener.ashx?v=111&f=earningsdate_tomorrowbefore&ft=4'
	#Combine pages for today after market close
	boolean = True
	num = 21
	dfTodayAfter = todayAfterMarketPage(todayAfter1)
	while (boolean):
		todayAfterNext = 'https://finviz.com/screener.ashx?v=111&f=earningsdate_todayafter&ft=4&r=' + str(num)
		df2 = todayAfterMarketPage(todayAfterNext)
		if (df2.shape[0]>1):
			frames = [dfTodayAfter,df2]
			dfTodayAfter = pd.concat(frames)
			num += 20
		else:
			break
	#Now combine pages for tomorrow before market open
	num = 21
	dfTomorrowBefore = tomorrowBeforeMarketPage(tmBefore1)
	while (boolean):
		tmBeforeNext = 'https://finviz.com/screener.ashx?v=111&f=earningsdate_tomorrowbefore&ft=4&r=' + str(num)
		df2 = tomorrowBeforeMarketPage(tmBeforeNext)
		if (df2.shape[0]>1):
			frames = [dfTomorrowBefore,df2]
			dfTomorrowBefore = pd.concat(frames)
			num += 20
		else:
			break
	#combine both today after and tomorrow before
	framesBig = [dfTodayAfter,dfTomorrowBefore]
	finalDF = pd.concat(framesBig)
	finalDF = finalDF.sort_values(by=['Stock Name'])
	del finalDF['Change']

	return finalDF

'''
 These functions get a stock in string type
 Returns a Ranking in string type
'''
def zacks(stock):
    url = 'https://www.zacks.com/stock/quote/' + str(stock).lower()
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'})
    soup = BeautifulSoup(r.content, "html.parser")
    search = soup.find_all("p", {"class": "rank_view"})
    count = 0
    str(search)
    if search == None or len(search) == 0:
        return None
    search = search[0]
    result = ''
    for item in search:
        count += 1
        result = str(item)
        break
    result = result.lstrip()
    return result

def yahoo(stock):
	url = 'https://finance.yahoo.com/quote/' + stock.upper() + '?p=' + stock.upper() + '&.tsrc=fin-srch'
	r = requests.get(url)
	soup = BeautifulSoup(r.content, "html.parser")
	soupStr = str(soup)
	str1 = "recommendationKey"
	spot = soupStr.find(str1)
	ans = soupStr[spot+20:spot+22]
	if ans == 'bu':
		ans2 = "BUY"
	elif ans == 'st':
		ans2 = "STRONG BUY"
	elif ans == 'ho':
		ans2 = "HOLD"
	elif ans == 'un':
		ans2 = "SELL"
	elif ans == 'se':
		ans2 = "STRONG SELL"
	else:
		ans2 = None
	return ans2

def theStreet(stock):
    url = 'https://www.thestreet.com/quote/' + str(stock).lower() + '.html'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'})
    soup = BeautifulSoup(r.content, "html.parser")
    search = soup.find_all("div", {"class": "quote-nav-rating-qr-label-container"})
    count = 0
    str(search)
    if search == None or len(search) == 0:
        return None
    search = str(search[0])
    search = re.sub('<[^>]+>', '', search)
    try:
        search.split()[4]
        search.split()[3]
    except IndexError:
        return None
    result = search.split()[3] + ' ' + search.split()[4]
    return (result)

def investor(stock):
	url = 'https://investorplace.com/stock-quotes/' + stock.lower() + '-stock-quote/'
	r = requests.get(url)
	soup = BeautifulSoup(r.content, "html.parser")
	search = soup.find_all("div", {"class":"grade grade-color"})
	search = re.sub('<[^>]+>', '', str(search))
	if (search[1]==']'):
		return None
	else:
		return(search[1])

'''
 These functions take in a list of stocks
 Returns a List of rankings from each website
'''
def zacksRankList(stockList):
	zacksList = []
	for i in range(len(stockList)):
		zacksList.append(zacks(stockList[i]))
	return zacksList

def yahooRankList(stockList):
	yahooList = []
	for i in range(len(stockList)):
		yahooList.append(yahoo(stockList[i]))
	return yahooList

def theStreetRankList(stockList):
	theStreetList = []
	for i in range(len(stockList)):
		theStreetList.append(theStreet(stockList[i]))
	return theStreetList

def investorRankList(stockList):
	investorList = []
	for i in range(len(stockList)):
		investorList.append(investor(stockList[i]))
	return investorList


'''
 This function creates a new CSV of all Companies EPSing tomorrow
 Saved on desktop
'''
def getTmRanks():
	df = combineAllPages()
	# stockList = df.index.values #gets the list of stocks
	stockList = df['Stock Name'].tolist() #gets the list of stocks
	zacksRanks = zacksRankList(stockList)
	print("Zacks Completed")
	yahooRanks = yahooRankList(stockList)
	print("Yahoo Completed")
	theStreetRanks = theStreetRankList(stockList)
	print("TheStreet Completed")
	investorRanks = investorRankList(stockList)
	print("InvestorRanks Completed")
	df['Zacks Ranks'] = zacksRanks
	df['Yahoo Ranks'] = yahooRanks
	df['The Street Ranks'] = theStreetRanks
	df['Investor Place'] = investorRanks
	mydate = datetime.datetime.now()
	myMonth = mydate.strftime("%B")
	myDay = datetime.datetime.today().day
	both = myMonth + str(myDay)
	df['Date'] = both
	#df.to_csv(str(myMonth) + str(myDay) + '-' + str(mydate.year-2000) + '-' + 'Rankings.csv', index=False)
	return df


####################################################################
####################################################################
##########  WEB-SCRAPE OTHER FINVIZ VALUATION PARAMETERS  ##########
####################################################################
####################################################################

'''IMPORTANT NOTE: Functions getListOfTickersToEPS(tmEPS) to return
the Stock List and getStockInfo(tmEPS) to return the stock 
information list from earlier still work. However function
infoToDataFrame(stockList, infoList) must be modified for each
different tab because of the amount of columns on each tab 
(ex. performance, technical, etc.) vary.
''' 

'''
These next five functions get the info from the five tabs on 
finviz and return a data frame
'''
def valInfoToDataFrame(page):
	stockList = getListOfTickersToEPS(page)
	if (len(stockList)==0):
		return pd.DataFrame()
	infoList = getStockInfo(page)
	finalList = []
	count = 0
	for i in range(1,len(stockList)+1):
		listOfList = []
		for z in range(17):
			listOfList.append(infoList[count])
			count += 1
		finalList.append(listOfList)
	df = pd.DataFrame(finalList, columns= ['Stock Count','Market Cap',
		'P/E','Fwd P/E','PEG','P/S', 'P/B','P/C','P/FCF','EPS this Y',
		'EPS next Y','EPS past 5Y','EPS next 5Y','Sales past 5Y','Price',
		'Change','Volume'])
	df.insert(loc=0,column="Stock Name",value=stockList)
	return df

def finInfoToDataFrame(page):
	stockList = getListOfTickersToEPS(page)
	if (len(stockList)==0):
		return pd.DataFrame()
	infoList = getStockInfo(page)
	finalList = []
	count = 0
	for i in range(1,len(stockList)+1):
		listOfList = []
		for z in range(17):
			listOfList.append(infoList[count])
			count += 1
		finalList.append(listOfList)
	df = pd.DataFrame(finalList, columns= ['Stock Count','Market Cap',
		'Divident','ROA','ROE','ROI', 'Curr R','Quick R','LTDebt/Eq','Debt/Eq',
		'Gross M','Oper M','Profit M','Earnings','Price','Change','Volume'])
	df.insert(loc=0,column="Stock Name",value=stockList)
	return df

def ownInfoToDataFrame(page):
	stockList = getListOfTickersToEPS(page)
	if (len(stockList)==0):
		return pd.DataFrame()
	infoList = getStockInfo(page)
	finalList = []
	count = 0
	for i in range(1,len(stockList)+1):
		listOfList = []
		for z in range(14):
			listOfList.append(infoList[count])
			count += 1
		finalList.append(listOfList)
	df = pd.DataFrame(finalList, columns= ['Stock Count','Market Cap',
		'Outstanding','Float','Insider Own','Insider Trans', 'Inst Own',
		'Inst Trans','Float Short','Short Ratio','Avg Volume','Price',
		'Change','Volume'])
	df.insert(loc=0,column="Stock Name",value=stockList)
	return df

def perfInfoToDataFrame(page):
	stockList = getListOfTickersToEPS(page)
	if (len(stockList)==0):
		return pd.DataFrame()
	infoList = getStockInfo(page)
	finalList = []
	count = 0
	for i in range(1,len(stockList)+1):
		listOfList = []
		for z in range(15):
			listOfList.append(infoList[count])
			count += 1
		finalList.append(listOfList)
	df = pd.DataFrame(finalList, columns= ['Stock Count','Perf Week',
		'Perf Month','Perf Quart','Perf Half','Perf Year', 'Perf YTD',
		'Volatility W','Volatility M','Recom','Avg Volume','Rel Volume',
		'Price','Change','Volume'])
	df.insert(loc=0,column="Stock Name",value=stockList)
	return df

def techInfoToDataFrame(page):
	stockList = getListOfTickersToEPS(page)
	if (len(stockList)==0):
		return pd.DataFrame()
	infoList = getStockInfo(page)
	finalList = []
	count = 0
	for i in range(1,len(stockList)+1):
		listOfList = []
		for z in range(14):
			listOfList.append(infoList[count])
			count += 1
		finalList.append(listOfList)
	df = pd.DataFrame(finalList, columns= ['Stock Count','Beta', 'ATR',
		'SMA20','SMA50','SMA200','52W High', '52W Low', 'RSI', 'Price',
		'Change','from Open', 'Gap','Volume'])
	df.insert(loc=0,column="Stock Name",value=stockList)
	return df

'''
This method will combine all the potential pages for each tab
combining both today after and tomorrow before (every page)
will return a data frame
'''
def combineValPages():
	valPageTodayAfter = 'https://finviz.com/screener.ashx?v=121&f=earningsdate_todayafter&ft=4'
	valPageTmBefore = 'https://finviz.com/screener.ashx?v=121&f=earningsdate_tomorrowbefore&ft=4'
	#Combine pages for today after market close
	boolean = True
	num = 21
	dfTodayAfter = valInfoToDataFrame(valPageTodayAfter)
	while(boolean):
		todayAfterNext = 'https://finviz.com/screener.ashx?v=121&f=earningsdate_todayafter&ft=4&r=' + str(num)
		df2 = valInfoToDataFrame(todayAfterNext)
		if (df2.shape[0]>1):
			frames = [dfTodayAfter,df2]
			dfTodayAfter = pd.concat(frames)
			num += 20
		else:
			break
	dfTodayAfter['EPS Time'] = "Today After Market EPS"
	#Now combine pages for tomorrow before market open
	num = 21
	dfTomorrowBefore = valInfoToDataFrame(valPageTmBefore)
	while (boolean):
		tmBeforeNext = 'https://finviz.com/screener.ashx?v=121&f=earningsdate_tomorrowbefore&ft=4&r=' + str(num)
		df2 = valInfoToDataFrame(tmBeforeNext)
		if (df2.shape[0]>1):
			frames = [dfTomorrowBefore,df2]
			dfTomorrowBefore = pd.concat(frames)
			num += 20
		else:
			break
	dfTomorrowBefore['EPS Time'] = "Tomorrow Before Market EPS"
	#combine both today after and tomorrow before
	framesBig = [dfTodayAfter,dfTomorrowBefore]
	finalDF = pd.concat(framesBig)
	finalDF = finalDF.sort_values(by=['Stock Name'])
	del finalDF['Change']
	return finalDF

def combineFinPages():
	finPageTodayAfter = 'https://finviz.com/screener.ashx?v=161&f=earningsdate_todayafter&ft=4'
	finPageTmBefore = 'https://finviz.com/screener.ashx?v=161&f=earningsdate_tomorrowbefore&ft=4'
	boolean = True
	num = 21
	dfTodayAfter = finInfoToDataFrame(finPageTodayAfter)
	while(boolean):
		todayAfterNext = 'https://finviz.com/screener.ashx?v=161&f=earningsdate_todayafter&ft=4&r=' + str(num)
		df2 = finInfoToDataFrame(todayAfterNext)
		if (df2.shape[0]>1):
			frames = [dfTodayAfter,df2]
			dfTodayAfter = pd.concat(frames)
			num += 20
		else:
			break
	dfTodayAfter['EPS Time'] = "Today After Market EPS"
	num = 21
	dfTomorrowBefore = finInfoToDataFrame(finPageTmBefore)
	while (boolean):
		tmBeforeNext = 'https://finviz.com/screener.ashx?v=161&f=earningsdate_tomorrowbefore&ft=4&r=' + str(num)
		df2 = finInfoToDataFrame(tmBeforeNext)
		if (df2.shape[0]>1):
			frames = [dfTomorrowBefore,df2]
			dfTomorrowBefore = pd.concat(frames)
			num += 20
		else:
			break
	dfTomorrowBefore['EPS Time'] = "Tomorrow Before Market EPS"
	framesBig = [dfTodayAfter,dfTomorrowBefore]
	finalDF = pd.concat(framesBig)
	finalDF = finalDF.sort_values(by=['Stock Name'])
	del finalDF['Change']
	return finalDF

def combineOwnPages():
	ownPageTodayAfter = 'https://finviz.com/screener.ashx?v=131&f=earningsdate_todayafter&ft=4'
	ownPageTmBefore = 'https://finviz.com/screener.ashx?v=131&f=earningsdate_tomorrowbefore&ft=4'
	boolean = True
	num = 21
	dfTodayAfter = ownInfoToDataFrame(ownPageTodayAfter)
	while(boolean):
		todayAfterNext = 'https://finviz.com/screener.ashx?v=131&f=earningsdate_todayafter&ft=4&r=' + str(num)
		df2 = ownInfoToDataFrame(todayAfterNext)
		if (df2.shape[0]>1):
			frames = [dfTodayAfter,df2]
			dfTodayAfter = pd.concat(frames)
			num += 20
		else:
			break
	dfTodayAfter['EPS Time'] = "Today After Market EPS"
	num = 21
	dfTomorrowBefore = ownInfoToDataFrame(ownPageTmBefore)
	while (boolean):
		tmBeforeNext = 'https://finviz.com/screener.ashx?v=131&f=earningsdate_tomorrowbefore&ft=4&r=' + str(num)
		df2 = ownInfoToDataFrame(tmBeforeNext)
		if (df2.shape[0]>1):
			frames = [dfTomorrowBefore,df2]
			dfTomorrowBefore = pd.concat(frames)
			num += 20
		else:
			break
	dfTomorrowBefore['EPS Time'] = "Tomorrow Before Market EPS"
	framesBig = [dfTodayAfter,dfTomorrowBefore]
	finalDF = pd.concat(framesBig)
	finalDF = finalDF.sort_values(by=['Stock Name'])
	del finalDF['Change']
	return finalDF

def combinePerfPages():
	perfPageTodayAfter = 'https://finviz.com/screener.ashx?v=141&f=earningsdate_todayafter&ft=4'
	perfPageTmBefore = 'https://finviz.com/screener.ashx?v=141&f=earningsdate_tomorrowbefore&ft=4'
	boolean = True
	num = 21
	dfTodayAfter = perfInfoToDataFrame(perfPageTodayAfter)
	while(boolean):
		todayAfterNext = 'https://finviz.com/screener.ashx?v=141&f=earningsdate_todayafter&ft=4&r=' + str(num)
		df2 = perfInfoToDataFrame(todayAfterNext)
		if (df2.shape[0]>1):
			frames = [dfTodayAfter,df2]
			dfTodayAfter = pd.concat(frames)
			num += 20
		else:
			break
	dfTodayAfter['EPS Time'] = "Today After Market EPS"
	num = 21
	dfTomorrowBefore = perfInfoToDataFrame(perfPageTmBefore)
	while (boolean):
		tmBeforeNext = 'https://finviz.com/screener.ashx?v=141&f=earningsdate_tomorrowbefore&ft=4&r=' + str(num)
		df2 = perfInfoToDataFrame(tmBeforeNext)
		if (df2.shape[0]>1):
			frames = [dfTomorrowBefore,df2]
			dfTomorrowBefore = pd.concat(frames)
			num += 20
		else:
			break
	dfTomorrowBefore['EPS Time'] = "Tomorrow Before Market EPS"
	framesBig = [dfTodayAfter,dfTomorrowBefore]
	finalDF = pd.concat(framesBig)
	finalDF = finalDF.sort_values(by=['Stock Name'])
	del finalDF['Change']
	return finalDF

def combineTechPages():
	techPageTodayAfter = 'https://finviz.com/screener.ashx?v=171&f=earningsdate_todayafter&ft=4'
	techPageTmBefore = 'https://finviz.com/screener.ashx?v=171&f=earningsdate_tomorrowbefore&ft=4'
	boolean = True
	num = 21
	dfTodayAfter = techInfoToDataFrame(techPageTodayAfter)
	while(boolean):
		todayAfterNext = 'https://finviz.com/screener.ashx?v=171&f=earningsdate_todayafter&ft=4&r=' + str(num)
		df2 = techInfoToDataFrame(todayAfterNext)
		if (df2.shape[0]>1):
			frames = [dfTodayAfter,df2]
			dfTodayAfter = pd.concat(frames)
			num += 20
		else:
			break
	dfTodayAfter['EPS Time'] = "Today After Market EPS"
	num = 21
	dfTomorrowBefore = techInfoToDataFrame(techPageTmBefore)
	while (boolean):
		tmBeforeNext = 'https://finviz.com/screener.ashx?v=171&f=earningsdate_tomorrowbefore&ft=4&r=' + str(num)
		df2 = techInfoToDataFrame(tmBeforeNext)
		if (df2.shape[0]>1):
			frames = [dfTomorrowBefore,df2]
			dfTomorrowBefore = pd.concat(frames)
			num += 20
		else:
			break
	dfTomorrowBefore['EPS Time'] = "Tomorrow Before Market EPS"
	framesBig = [dfTodayAfter,dfTomorrowBefore]
	finalDF = pd.concat(framesBig)
	finalDF = finalDF.sort_values(by=['Stock Name'])
	del finalDF['Change']
	return finalDF

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
	print("All Rankings Complete: 1/6")
	valDF = combineValPages()
	print("Valuation Complete: 2/6")
	finDF = combineFinPages()
	print("Financial Complete: 3/6")
	ownDF = combineOwnPages()
	print("Ownership Complete: 4/6")
	perfDF = combinePerfPages()
	print("Performance Complete: 5/6")
	techDF = combineTechPages()
	print("Technical Complete: 6/6")
	
	result = pd.concat([rankingsDF,valDF,finDF,ownDF,perfDF,techDF], axis=1, join='inner')
	result = result.loc[:,~result.columns.duplicated()]
	mydate = datetime.datetime.now()
	myMonth = mydate.strftime("%B")
	myDay = datetime.datetime.today().day
	result.to_csv(str(myMonth) + str(myDay) + '-' + str(mydate.year-2000) + '-' + 'AllPredictors.csv', index=False)
	return result

####################################################################
####################################################################
############  FUNCTIONS FOR RESULTS AFTER EPS BELOW  ###############
####################################################################
####################################################################

'''
 This helper function takes a page
 Returns a Dataframe
'''
def resultsDF(page):
	stockList = getListOfTickersToEPS(page)
	if (len(stockList)==0):
		return pd.DataFrame()
	infoList = getStockInfo(page)
	df = infoToDataFrame(stockList,infoList) 
	return df

'''
 This function gets the results from today
 creates a CSV with todays date "-Results"
 Returns a dataframe
'''
def getResults():
	todayBefore1 = 'https://finviz.com/screener.ashx?v=111&f=earningsdate_todaybefore&ft=4'
	yesterdayAfter1 = 'https://finviz.com/screener.ashx?v=111&f=earningsdate_yesterdayafter&ft=4'
	#Combine pages for today after market close
	boolean = True
	num = 21
	dfTodayBefore = resultsDF(todayBefore1)
	while (boolean):
		todayBeforeNext = 'https://finviz.com/screener.ashx?v=111&f=earningsdate_todaybefore&ft=4&r=' + str(num)
		df2 = resultsDF(todayBeforeNext)
		if (df2.shape[0]>1):
			frames = [dfTodayBefore,df2]
			dfTodayBefore = pd.concat(frames)
			num += 20
		else:
			break
	#Now combine pages for tomorrow before market open
	num = 21
	dfYesterdayAfter = resultsDF(yesterdayAfter1)
	while (boolean):
		yesterdayAfterNext = 'https://finviz.com/screener.ashx?v=111&f=earningsdate_yesterdayafter&ft=4&r=' + str(num)
		df2 = resultsDF(yesterdayAfterNext)
		if (df2.shape[0]>1):
			frames = [dfYesterdayAfter,df2]
			dfYesterdayAfter = pd.concat(frames)
			num += 20
		else:
			break
	#combine both today after and tomorrow before
	framesBig = [dfTodayBefore,dfYesterdayAfter]
	finalDF = pd.concat(framesBig)
	finalDF = finalDF.sort_values(by=['Stock Name'])
	finalDF = finalDF[['Stock Name', 'Change']]
	mydate = datetime.datetime.now()
	myMonth = mydate.strftime("%B")
	myDay = datetime.datetime.today().day
	both = myMonth + str(myDay)
	finalDF['Date'] = both
	finalDF.to_csv(str(myMonth) + str(myDay) + '-' + str(mydate.year-2000) + '-' + 'Results.csv', index=False)
	return finalDF

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
	df1 = pd.read_csv(str(myMonth) + str(myDay-1) + '-' + str(mydate.year-2000) + '-' + 'AllPredictors.csv')
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
	#df1.to_csv(str(myMonth) + str(myDay) + '-' + str(mydate.year-2000) + '-' + 'Combined.csv')
	return df1


'''
 This function will combine two complete CSVs into the Ultimate EPS
'''
def ultimateCSV():
	mydate = datetime.datetime.now()
	myMonth = mydate.strftime("%B")
	myDay = datetime.datetime.today().day
	with open("/Users/ryandundun/Desktop/stockScripts/stockSpot.csv") as spot:
		reader = csv.reader(spot)
		spot = int(next(reader)[0])
	df1 = pd.read_csv('stockData' + str(spot) + '.csv')
	df2 = combinePredictorsAndResultsToCSV()
	frames = [df1,df2]
	newDF = pd.concat(frames)
	newDF = newDF[['Stock Name', 'Date', 'Change', 'Sector', 'Market Cap','Zacks Ranks','Yahoo Ranks', 'The Street Ranks',
	'Investor Place','Company', 'Industry','Country', 'P/E', 'Price', 'Volume', 'EPS Time','EPS next 5Y', 'EPS next Y', 
	'EPS past 5Y', 'EPS this Y', 'Fwd P/E', 'P/B', 'P/C', 'P/FCF', 'P/S', 'PEG', 'Sales past 5Y','Curr R', 'Debt/Eq', 
	'Divident', 'Earnings', 'Gross M', 'LTDebt/Eq', 'Oper M', 'Profit M','Quick R', 'ROA', 'ROE', 'ROI', 'Avg Volume',
	'Float', 'Float Short', 'Insider Own','Insider Trans', 'Inst Own', 'Inst Trans', 'Outstanding', 'Short Ratio', 
	'Perf Half','Perf Month', 'Perf Quart', 'Perf Week', 'Perf YTD', 'Perf Year', 'Recom', 'Rel Volume','Volatility M',
	'Volatility W', '52W High', '52W Low', 'ATR', 'Beta', 'Gap', 'RSI','SMA20', 'SMA200', 'SMA50', 'from Open']]
	newSpot = spot + 1
	fc = csv.writer(open('stockSpot.csv', 'w'))
	fc.writerow([newSpot])
	#newDF = newDF.drop_duplicates()
	newDF.to_csv('stockData'+ str(newSpot) +'.csv', index=False)



