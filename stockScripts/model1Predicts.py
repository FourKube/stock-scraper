#!/usr/bin/env python
# coding: utf-8
'''
This Model will have two bins up or down

'''
####    TO DO:
# Add cooks distance and other methods to remove outliers
# run cluster analysis to see what other data to include/remove
#  mess around with just using USA and other more predictive industries with less entropy


#pandas for data analysis
import pandas as pd
#to scale data
from sklearn.preprocessing import StandardScaler
#to encode data (categorical to numerical)
from sklearn.preprocessing import LabelEncoder
#to plot data
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder
from sklearn import svm
import numpy
import re
import numpy as np
import datetime
import csv
import requests
from bs4 import BeautifulSoup

#To get stock info from yahoo
#from yahoo_fin import stock_info as si
#from yahoo_fin.stock_info import get_analysts_info

# Import train_test_split function
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

#MAKE NEW PREDICTIONS
import sklearn
import matplotlib.pyplot as plt
from sklearn.utils.multiclass import unique_labels

#Import scikit-learn metrics module for accuracy calculation
from sklearn import metrics

#########################################################################
#########################################################################
#########################  READ IN DATA  ################################
#########################################################################
#########################################################################

with open("/Users/ryandundun/Desktop/stockScripts/stockSpot.csv") as spot:
        reader = csv.reader(spot)
        spot = int(next(reader)[0])

#with open("/Users/ryandundun/Desktop/stockScripts/stockData" + str(spot) + ".csv") as rawDataToModel:

rawDataToModel = pd.read_csv("/Users/ryandundun/Desktop/epsData/stockData"+str(spot)+".csv")

#########################################################################
#########################################################################
######################### GLOBAL VARIABLES ##############################
#########################################################################
#########################################################################



#Scale words into numerical heirarchies
scale_mapper_zacks = {'5-StrongSell': 1, 
                '4-Sell': 2,
                '3-Hold': 3,
                '2-Buy': 4,
                '1-StrongBuy': 5}
scale_mapper_yahoo = {'STRONG SELL': 1,
                'SELL': 2, 
                'UNDERPERFORM': 3,
                'HOLD': 4,
                'BUY': 5,
                'STRONG BUY': 6}
scale_mapper_thestreet = {'(Sell)': 1, 
                '(Hold)': 2,
                '(Buy)': 3}
scale_mapper_investor = {'F': 1, 
                'D': 2,
                'C': 3,
                'B': 4,
                'A': 5}


# bins to put predictions into
bins = [-1000,0, 1000]

#I think it Makes the One and 0 labels. ask richard tho
labels = np.arange(0, len(bins) - 1)

#########################################################################
#########################################################################
############################ DATA PREP ##################################
#########################################################################
#########################################################################

'''
Only include United States Companies
'''
def only_US_companies(df):
    df = df[df['Country'] == 'USA']
    return df
    

'''
Only these columns. 
'''
def chooseColumns(df):
    df = df[['Stock Name', 'Change', 'Zacks Ranks', 'Yahoo Ranks', 'The Street Ranks', 'Investor Place']].copy()
    return df
'''
Cleans up The Street Rating ratings from B+ Buy to Sell, Hold, or Buy
'''
def streetRate(row):
    val = row["The Street Ranks"]
    match = re.search(r'\(\w+\)', val) # found, match.group() == "123"
    if match:
        return match.group()
    else:
        return None

'''
Applying One Hot Encoding and replacing Data with one hot encoding scale
'''
def applyScaling(df): 
    df['streetRating'] = df.apply (lambda row: streetRate(row), axis=1)
    df['Zacks Ranks'] = df['Zacks Ranks'].str.replace(" ","")
    df['scaleZacks'] = df['Zacks Ranks'].replace(scale_mapper_zacks)
    df['scaleYahoo'] = df['Yahoo Ranks'].replace(scale_mapper_yahoo)
    df['scaleStreet'] = df['streetRating'].replace(scale_mapper_thestreet)
    df['scaleInvestor'] = df['Investor Place'].replace(scale_mapper_investor)
    return df

'''
Drop columns with empty  values. Seems like model performs
better without yahoo as of now 9/18
'''
def dropEmptyData(df):
    df = df.dropna()
    #df = df.mask(df.eq('None')).dropna() #this is yahoo
    #df = df.mask(df.eq('Total Grade:')).dropna()
    df = df.mask(df.eq(']')).dropna()
    df = df.mask(df.eq('None')).dropna()
    return df

'''
Makes a pricediff column that is Change column without percentages
Makes Results column which puts pricediff into global var bins define above
'''
def addResultColumn(df):
    #remove % signs and convert to numerical var (float)
    df['pricediff'] = df['Change'].str[:-1]
    df['pricediff'] = df['pricediff'].astype(float)
    #Convert Purchase (labels) to categories
    df["results"] = pd.cut(df["pricediff"], bins=bins,labels=labels)
    df['results'].unique()

    df.reset_index(drop=True, inplace=True)
    #df = df.drop(['Change', 'pricediff'], axis=1)
    return df

#########################################################################
#########################################################################
############### MAKE THE MACHINE LEARNING MODEL #########################
#########################################################################
#########################################################################

'''
Random Forest Model is made here
Data is split into X~Features and Y~Labels and then split again 
into training and test data
'''
def makeRF_model(df, test_size):
    #predictor vars. features
    #Features
    #X = df[['scaleZacks', 'scaleYahoo', 'scaleStreet', 'scaleInvestor']].copy()
    X = df[['scaleZacks', 'scaleStreet', 'scaleInvestor']].copy()
    X = np.array(X)

    #labels
    y = np.array(df['results'])

    #Split dataset into training set and test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=5) 

    #create RF model
    clf = RandomForestClassifier(n_estimators=1000)
    clf.fit(X_train, y_train)


    #model predictions
    y_pred=clf.predict(X_test)

    # Model Accuracy, how often is the classifier correct?
    theAccuracy = metrics.accuracy_score(y_test, y_pred)
    print("Accuracy:",metrics.accuracy_score(y_test, y_pred))
    return clf, theAccuracy, y_pred, y_test

'''
This calculates the accuracy of how often the model is at its 
predictions when it decides to buy. This is valuable because 
all we care about is if the model is right when it tells us
to buy, not necesarily if we just 'miss out' on a buy when
the model says don't buy.
Args: y_pred - model predictions
      y_test - true results
Returns: swingAccuracy: how accurate model is when it says buy
'''
def getSwingAccuracy(y_pred,y_test):
    swung = 0
    correct = 0
    for i in range(len(y_pred)):
        if (y_pred[i]==1):
            swung += 1
            if (y_test[i]==1):
                correct +=1 
    swing_accuracy = (correct/swung)
    return swing_accuracy


#########################################################################
#########################################################################
#################### BUY AND SELL STOCKS ################################
#########################################################################
#########################################################################


'''
Get the live price of any stock by webscraping zacks
'''
def getLiveStockPrice(stock):
    url = 'https://www.zacks.com/stock/quote/' + str(stock).lower()
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'})
    soup = BeautifulSoup(r.content, "html.parser")
    search = soup.find_all("p", {"class": "last_price"})
    price = search[0].text
    price = re.sub('USD', '', price)
    price = price[1:]
    price = price.strip()
    return price

'''
Pretend to buy stocks
'''
def paperBuy(finalDF):
    mydate = datetime.datetime.now()
    myMonth = mydate.strftime("%B")
    myDay = datetime.datetime.today().day
    finalDF.to_csv('paperBuy-' + str(myMonth) + str(myDay) + '-' + str(mydate.year-2000) + '.csv')
    #finalDF.to_csv('tryForThursdayMorning2.csv')

'''
Pretend to sell stocks
'''
def paperSell(finalDF):
    
    #oldPaperTrade = pd.read_csv('paperTrade-September8-19.csv')
    paperBuy = pd.read_csv('paperBuy-' + str(myMonth) + str(myDay-2) + '-' + str(mydate.year-2000) + '.csv')
    
    
    paperBuy.columns = ["Stock Name","Prediction","Buying Price"]
    listOfBuys = paperBuy["Stock Name"].tolist()

    currentPriceList = []
    for i in listOfBuys:
        currentPrice = getLiveStockPrice(i)
        currentPriceList.append(currentPrice)

    paperBuy['Selling Price'] = currentPriceList
    print(paperBuy)
    paperBuy.to_csv('tryForThursdayMorning.csv', index=False)

#########################################################################
#########################################################################
#################  VISUALIZATIONS AND PLOTS  ############################
#########################################################################
#########################################################################

'''
Makes Confusion Matrix.
Matrix is best when is diagonal
'''
def plot_confusion_matrix(y_true, y_pred, classes,
                          normalize=False,
                          title=None,
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if not title:
        if normalize:
            title = 'Normalized confusion matrix'
        else:
            title = 'Confusion matrix, without normalization'

    # Compute confusion matrix
    cm = sklearn.metrics.confusion_matrix(y_true, y_pred)
    # Only use the labels that appear in the data
    classes = classes[unique_labels(y_true, y_pred)]
    #classes = ["\$0-\$5886", "\$5886-\$8062", "\$8062-\$12074", "\$12074-\$24000"]
    #[0, 5886, 8062, 12074, 24000]
    classes = ["Q1", "Q2", "Q3", "Q4"]
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

#     print(cm)

    fig, ax = plt.subplots()
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)
    # We want to show all ticks...
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           # ... and label them with the respective list entries
           xticklabels=classes, yticklabels=classes,
           title=title,
           ylabel='True label',
           xlabel='Predicted label')

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    return ax

def makePlots(finalDF):
    classes = labels
    plot_confusion_matrix(y_test, y_pred, classes, normalize=True)

    #Plots 
    #barPlot = finalDF.plot.bar()
    #plt.show()
    #matplotlib.pyplot.show()
    pass

def makeSimpleBuyOrDontBuyPlot(df):
    barPlot = df.plot.bar(y='Prediction')
    plt.savefig('bb.jpg')

#########################################################################
#########################################################################
#####################  MAKE NEW PREDICTIONS  ############################
#########################################################################
#########################################################################
'''
Choose the Number of bins
'''
def chooseBins(numBins):
    if (numBins==2):
        bins = [-1000,3, 1000]
    elif (numBins==4):
        bins = [-1000,-3,0,3,1000]
    elif (numBins==6):
        bins = [-1000,-6,-3,0,3,6,1000]
    else:
        return False
    return bins


#new
cleanData = dropEmptyData(rawDataToModel)
print(len(cleanData))
cleanData = only_US_companies(cleanData)
print(len(cleanData))
print(cleanData)

cleanData = applyScaling(cleanData)


cleanData = addResultColumn(cleanData)



clf, theAccuracy, y_pred, y_test = makeRF_model(cleanData, 0.25)

print(theAccuracy)

#print('prediction was: '+str(y_pred))
#print('actual result : '+str(y_test))
#is swing accuracy and normal accuracy same when bot is 50/50?
swung = 0
correct = 0

for i in range(len(y_pred)):
    print(str(y_test[i]) + ' ' + str(y_pred[i]))
    if (y_pred[i]==1):
        swung += 1
        if (y_test[i]==1):
            correct +=1 

swing_accuracy = (correct/swung)
print('swing accuracy: '+str(swing_accuracy))
classes=labels
#plot_confusion_matrix(y_test, y_pred, classes, normalize=True)



todaysPredictionData = pd.read_csv("/Users/ryandundun/Desktop/epsData/June26-19-AllPredictors.csv")
todaysPredictionData = applyScaling(todaysPredictionData)
todaysPredictionData = dropEmptyData(todaysPredictionData)
todaysPredictionData = only_US_companies(todaysPredictionData)

print(todaysPredictionData)

newX = todaysPredictionData[['scaleZacks', 'scaleStreet', 'scaleInvestor']].copy()
priceList = todaysPredictionData['Price'].tolist()
prediction=clf.predict(newX)
predList=prediction.tolist()

print(predList)

stockList= todaysPredictionData['Stock Name'].tolist()
finalDF = pd.DataFrame(predList, index=stockList)
finalDF['Price'] = priceList
finalDF.columns=['Prediction','Buying Price']
print(finalDF)

makeSimpleBuyOrDontBuyPlot(finalDF)

#filter data frame for only stocks to buy
#finalDF = finalDF.query('Prediction==1')

# paperBuy(finalDF)


#end new


# mydate = datetime.datetime.now()
# myMonth = mydate.strftime("%B")
# myDay = datetime.datetime.today().day
# #newData = pd.read_csv(str(myMonth) + str(myDay) + '-' + str(mydate.year-2000) + '-' + 'AllPredictors.csv')
# predictionData = 'September17-19-AllPredictors.csv'
# newData = pd.read_csv(predictionData)

# #X_test.head() #want it to look like this


# newData['streetRating'] = newData.apply (lambda row: streetRate(row), axis=1)
# newData['Zacks Ranks'] = newData['Zacks Ranks'].str.replace(" ","")
# newData['scaleZacks'] = newData['Zacks Ranks'].replace(scale_mapper_zacks)
# newData['scaleYahoo'] = newData['Yahoo Ranks'].replace(scale_mapper_yahoo)
# newData['scaleStreet'] = newData['streetRating'].replace(scale_mapper_thestreet)
# newData['scaleInvestor'] = newData['Investor Place'].replace(scale_mapper_investor)
# newData = newData.dropna()
# #newData = newData.mask(newData.eq('None')).dropna()  #this is yahoo
# newData = newData.mask(newData.eq('Total Grade:')).dropna()
# newData = newData.mask(newData.eq(']')).dropna()


# #newX = newData[['scaleZacks', 'scaleStreet', 'scaleInvestor','scaleYahoo']].copy()
# newX = newData[['scaleZacks', 'scaleStreet', 'scaleInvestor']].copy()
# priceList = newData['Price'].tolist()


# #print(newX)
# prediction=clf.predict(newX)
# print("data is")
# print(newData)
# print("prediction is")
# print(prediction)


# predList=prediction.tolist()
# stockList= newData['Stock Name'].tolist()
# #print(len(predList))
# #print(len(stockList))


# finalDF = pd.DataFrame(predList, index=stockList)
# finalDF['Price'] = priceList
# finalDF.columns=['Prediction','Buying Price']
# print(finalDF)

# #filter data frame for only stocks to buy
# finalDF = finalDF.query('Prediction==1')



