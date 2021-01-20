import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import math
from scipy.stats import poisson, expon
from pandas import json_normalize
from functools import reduce
import fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import os
import tabulate
import time
import warnings

warnings.filterwarnings("ignore") 

def matching(arrayStrOne,arrayStrTwo):
	matches = []
	for i in arrayStrOne:
		attempt = [fuzz.token_sort_ratio(str(i), str(j)) for j in arrayStrTwo]
		#print(attempt)
		matches += [arrayStrTwo[np.argmax(attempt)]]
	return matches

def Kelly(oddsDecimal, probability):
  return (oddsDecimal*probability - (1-probability))/oddsDecimal

def reverseKelly(payout, Kelly):
	return( (kelly * payout -1)/(1+payout) )

def reverseOdds(dec):
	if dec>2:
		val = (dec - 1)*100
		return "+" + str(int(val))
	else:
		val = 100/(dec - 1)
		return "-" + str(int(val))
	
def powerLaw(portfolioAmt,df):
  probs = np.array([(1-(1/i)) for i in df['Payouts (per Dollar)'].values]) #can be used for higher risk tolerance though unused here
  amount = 1/np.prod(probs) #test portfolio constraints
  kelly = df['Kelly Criterion Suggestion'].values
  #spread = df['Probability Spread'].values
  allocation1 = [np.minimum((portfolioAmt*i)*(i/np.sum(kelly)), 0.3*portfolioAmt) for i in kelly] #RISK TOLERANCE ESTABLISHED HERE 
  df['Allocation Dollars'] = allocation1
  #print('Total Allocated', np.sum(allocation1).round(decimals=2), 'out of', portfolioAmt)
  df['Allocation Percentage'] = [(i/portfolioAmt) for i in allocation1]
  return df

def gainsLosses(allocation,successes, df, portfolio):
  payouts = df['Payouts (per Dollar)'].values
  prev = np.sum(allocation)
  now = np.sum(np.dot([allocation[i]*payouts[i] for i in range(len(payouts))], successes))
  return [portfolio+(now-prev), prev, now]

		
def dailyReturn():
	if (input("Are you here to update? ").lower() == 'yes'):
		port = pd.read_csv(os.getcwd() + '/masterPortfolio.csv')
		portfolioAmt = port.Portfolio.values[-1]
		array = [int(item) for item in input("Enter the list items : ").split()] #this shhould come from gamBet
		today = str(date.today() - timedelta(1)) #works until 00:00 same day
		portfolioTrack = pd.read_csv(os.getcwd() + '/masterDaily.csv')
		portfolioTracker = portfolioTrack[portfolioTrack.Date == today]
		#print(len(portfolioTracker))
		portfolioTracker["Success"] = array
		#print(portfolioTracker)
		portfolioTracker.to_csv(os.getcwd() + '/masterDaily.csv', mode = 'a', index = False, header = False)
		portfolioTracked = pd.read_csv(os.getcwd() + '/masterDaily.csv')
		#print(portfolioTracked)
		portfolioTracked = portfolioTracked.drop_duplicates(subset=['Bet State Chosen', 'League'], keep='last')
		portfolioTracked = portfolioTracked.sort_values(['Date', 'League'])
		portfolioTracked.to_csv(os.getcwd() + '/masterDaily.csv', index = False)
		print(portfolioTracked)
		#this is the calculation	
		port = pd.read_csv(os.getcwd() + '/masterPortfolio.csv')
		portfolioAmt = port.Portfolio.values[-1]
		portfolioTracked = pd.read_csv(os.getcwd() + '/masterDaily.csv')
		today = str(date.today() - timedelta(1))
		portfolioTracking = portfolioTracked[portfolioTracked.Date == today]
		bet = powerLaw(portfolioAmt, portfolioTracking)
		bet.to_csv(os.getcwd() + '/masterDailyRecap.csv')
		returns = gainsLosses(bet['Allocation Dollars'].values,bet['Success'].values, portfolioTracking, portfolioAmt)
		print(portfolioAmt)
		updates = [returns[0]]
		change = [returns[2]/returns[1]]
		print('With a total portfiolio of now ',returns[0].round(2), ' we bet ', returns[1].round(2), ' which became ',returns[2].round(2), ' for an ROE of ', ((change[0]-1)*100).round(2), '%')
		
		resulting = pd.DataFrame({'Day':[port.Day.values[-1]+1],'Portfolio':updates, 'Change':change})
		resulting.to_csv(os.getcwd() + '/masterPortfolio.csv', mode='a', header=False, index = False)
		return 'Done'
	
	else: 
		port = pd.read_csv(os.getcwd() + '/masterPortfolio.csv')
		portfolioAmt = port.Portfolio.values[-2]
		portfolioTracked = pd.read_csv(os.getcwd() + '/masterDaily.csv')
		today = str(date.today() - timedelta(1))
		portfolioTracking = portfolioTracked[portfolioTracked.Date == today]
		bet = powerLaw(portfolioAmt, portfolioTracking).round(3)
		bet.to_csv(os.getcwd() + '/masterDailyRecap.csv')
		
		tomorrow = str(date.today())
		portfolioTrackingTom = portfolioTracked[portfolioTracked.Date == tomorrow]
		bettor = powerLaw(portfolioAmt, portfolioTrackingTom).round(5)
		bettor.to_csv(os.getcwd() + '/masterUpcoming.csv')
		bettors = bettor[['Bet State Chosen', 'Allocation Percentage', 'League', 'Payouts (per Dollar)', 'Date']]
		bettors['Allocation Percentage'] = [i*100 for i in bettors['Allocation Percentage']]
		bettors = bettors.round(4)
		bettors['American Odds'] = [reverseOdds(i) for i in bettors['Payouts (per Dollar)']]
		bettors['Update Time (EST)'] = [str(datetime.now().strftime("%H:%M:%S")) for i in range(len(bettors))]
		bettors = bettors[bettors['Allocation Percentage'] > 0.001]
		bettors.to_csv(os.getcwd() + '/masterPush.csv')
		
		returns = gainsLosses(bet['Allocation Dollars'].values,bet['Success'].values, portfolioTracking, portfolioAmt)
		print(portfolioAmt, ' portfolio amount of the day.')
		updates = [returns[0]]
		change = [returns[2]/returns[1]]
		print('With a total portfiolio of now ',returns[0].round(2), ' we bet ', returns[1].round(2), ' which became ',returns[2].round(2), ' for an ROE of ', ((change[0]-1)*100).round(2), '%')
		return 'Done'
	
	
	
	

'''
To do:
-- comment some more stuff and figure out hwo to implement NHl in this exact framework, maybe jsut replace the XHR, but the bettting is different, run seperately?
-- add over under, period bets, make the names for tie more clear if possible
-- make tree structure easy to implement

Notes:
-- this will force people to make a directory or maybe to have a folder called data in place, thinking of possible easy of application
'''

#Make a time function

def run():
	return (dailyReturn())


	
