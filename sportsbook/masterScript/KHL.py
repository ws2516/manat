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


def matching(arrayStrOne,arrayStrTwo):
	matches = []
	for i in arrayStrOne:
		attempt = [fuzz.token_sort_ratio(str(i), str(j)) for j in arrayStrTwo]
		#print(attempt)
		matches += [arrayStrTwo[np.argmax(attempt)]]
	return matches
	
def getScore(daysBack):
  output = []
  page = 1
  delta = 0
  time.sleep(10)
  while(delta<daysBack):
    if page ==1:
      time.sleep(10)
      url = 'https://betsapi.com/le/128/KHL'
    else:
      time.sleep(10)
      url = 'https://betsapi.com/le/128/KHL'+'/p.'+str(page)
    #print(url)
    page_response = requests.get(url, timeout=10,  headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9,fr;q=0.8,ro;q=0.7,ru;q=0.6,la;q=0.5,pt;q=0.4,de;q=0.3',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'})
    page_content = BeautifulSoup(page_response.content, "html.parser")
    #print(page_content)
    latest_date_on_page = page_content.findAll('td', class_ = "dt_n")[-1]['data-dt'][:10] #given as YYYY-MM-DD
    f_date = date(int(latest_date_on_page[:4]), int(latest_date_on_page[5:7]), int(latest_date_on_page[-2:]))
    get_today = date.today().strftime('%Y-%m-%d')
    l_date = date(int(get_today[:4]), int(get_today[5:7]), int(get_today[-2:]))
    delta = l_date - f_date

    div_scores = [i.text for i in page_content.findAll('a')]
    start = div_scores.index('Top Lists')
    
    if page ==1:
      end = div_scores.index(str(page))
    else:
      end = div_scores.index('« Prev')
    delta = delta.days
    page += 1
    output+= div_scores[start+1:end]
  return output

def to_dataframe(listing):
  home, away, scoreH, scoreA = [], [], [], []
  for i in range(len(listing)):
      #print(i%3, listing[i])
      if i%3 ==0:
        home.append(listing[i].lower())
      elif i%3 == 1:
        away.append(listing[i].lower())
      else:
        score = listing[i].split('-')
        #print(score)
        if len(score) ==2:
          scoreH.append(int(score[0].strip()))
          scoreA.append(int(score[1].strip()))
        else:
          scoreH.append(np.NaN)
          scoreA.append(np.NaN)
  gameLog = pd.DataFrame({'gameDate':[i for i in range(len(home))],'Home':home, 'Away':away,'HomeGoals':scoreH,'AwayGoals':scoreA})
  #print(gameLog)
  return gameLog.dropna()

def df_of_the_day(daysBack):
  raw_text = getScore(daysBack)
  #print(raw_text)
  df = to_dataframe(raw_text)
  #print(df)
  return df
  
def teamNamesKHL(jsonData): #0 same day, 1 next day
    results_df = pd.DataFrame()
    teams = []
    for alpha in jsonData['events']:
    	#print(date.strftime(date.today(), "%Y-%m-%d"))
    	#print(alpha['tsstart'][:10])
    	if (alpha['tsstart'][:10] == date.strftime(date.today(), "%Y-%m-%d")):
    		teams += [alpha['participantname_away'],alpha['participantname_home']]
    return pd.DataFrame({'id':[i.lower() for i in np.unique(teams)]})#time right for <7 on prev day

def parse_data(jsonData):
    results_df = pd.DataFrame()
    for alpha in jsonData['events']:
        gameday = (alpha['tsstart'][:10])
        check = str(date.today())
        #print(gameday,check,'hello')
        if gameday == check:
        	print ('Gathering %s data: %s @ %s' %(alpha['sportname'],alpha['participantname_away'],alpha['participantname_home']))
        	alpha_df = json_normalize(alpha).drop('markets',axis=1)
        	for beta in alpha['markets']:
        		beta_df = json_normalize(beta).drop('selections',axis=1)
        		beta_df.columns = [str(col) + '.markets' for col in beta_df.columns]
        		for theta in beta['selections']:
        			theta_df = json_normalize(theta)
        			theta_df.columns = [str(col) + '.selections' for col in theta_df.columns]
        			
        			temp_df = reduce(lambda left,right: pd.merge(left,right, left_index=True, right_index=True), [alpha_df, beta_df, theta_df])
        			results_df = results_df.append(temp_df, sort=True).reset_index(drop=True)

    return results_df #time right for <7 on prev day

def fullSet(eventID):
  return requests.get('https://sportsbook.fanduel.com//cache/psevent/UK/1/false/'+ str(eventID) + '.json').json()

def build(oddsDataFrame,GoalsLookup):
  betting = []
  for i in range(len(oddsDataFrame.iloc[:,0].values)):
    betName = oddsDataFrame.iloc[:,1].values[i]
    game = oddsDataFrame.iloc[:,0].values[i]
    for i in oddsDataFrame.iloc[i,2:].values:
      if i!=None:
        betting += [betFunction(game, betName,i, GoalsLookup)]
  df = pd.DataFrame(betting).dropna()
  df = df.reset_index()
  df.columns = ['Bet Number','Game','Team','DecimalOdds','Type']
  return df
  
def getOdds(listing):
  bets = []
  for game in listing:
    for i in game['eventmarketgroups'][0]['markets']:
      betName = [game['externaldescription'], i['name']]
      for i in i['selections']:
        #print(i)
        betName+=[[i['name'], (i['currentpriceup']/i['currentpricedown'])]] #, i['currenthandicap']
      bets += [betName]
  return bets

def fetch():
  jsonData_fanduel_khl = requests.get('https://sportsbook.fanduel.com/cache/psmg/UK/63782.3.json').json() #gives the game id
  khl = parse_data(jsonData_fanduel_khl)
  #print(khl)
  teamID = fetchName()
  GoalsLookup = pd.merge(fetchName(), teamLookBackGoals(teamID,21), on='ID')
  KHL = pd.DataFrame(khl)[['eventname','tsstart','idfoevent.markets']]
  KHL.columns = ['Teams','Date','EventID']
  listing = []
  for i in np.unique(KHL.EventID.values): #pulls all odds for the specified game
    listing.append((fullSet(i)))
  return build(pd.DataFrame(getOdds(listing)),GoalsLookup) #catch for the XHR change

def fetchName(): 

  jsonData_fanduel_khl = requests.get('https://sportsbook.fanduel.com/cache/psmg/UK/63782.3.json').json() #gives the game id
  url = 'https://betsapi.com/l/128/KHL'
  #print('hello')
  page_response = requests.get(url, timeout=10, headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9,fr;q=0.8,ro;q=0.7,ru;q=0.6,la;q=0.5,pt;q=0.4,de;q=0.3',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'})
  page_content = BeautifulSoup(page_response.content, "html.parser")
  #print(page_content)
  dates = [(i.text).split(' ')[0] for i in page_content.findAll('td', class_ = "dt_n")]
  teaming = [j.findAll('a') for j in [i for i in page_content.findAll('tr')][1:]]
  #teams = [[j.text for j in i] for i in teaming]
  teams = [(i.text).strip().lower() for i in page_content.findAll('a')]
  #print(teams)
  if(True): #fix this
  	array = []
  	for i in range(1,15):
  		try:
  			current_day = datetime.now() + timedelta(days=i)
  			#print(current_day)
  			formatted_date = date.strftime(current_day, "%m/%d")
  			num_games_today = dates.index(formatted_date)
  			array +=['y']
  		except:
  			array += ['n']
  			#print(array)
  else:
  	current_day = datetime.now() + timedelta(days=array.index('y')+1)
  	formatted_date = date.strftime(current_day, "%m/%d")
  	num_games_today = dates.index(formatted_date)
  start = teams.index('table') + 3
  shift = num_games_today*3
  newest = teams[start:start+shift]
  #print(newest, 'hereeee')

  #print('boooooo')
  khl = teamNamesKHL(jsonData_fanduel_khl)
  #print(khl)
  namesweb = np.sort([i for i in teams[start:start+shift] if i != 'view'])
  #print(namesweb)
  sortedNames = matching(khl.id.values,namesweb)
  khl['ID'] = sortedNames
  #print(khl)
  return khl #time delta right for being run <7 on prev day

def Poisson(mu,discreteStep):
  poiArray = [poisson(mu).pmf(x) for x in range(discreteStep)]
  poiArray.append(1-sum(poiArray))
  return poiArray

def poissonMatrix(avGoalsHome,avGoalsAway):
  Home = np.array(Poisson(avGoalsHome,7))
  Away = np.array(Poisson(avGoalsAway,7)).reshape(len(Home),1)
  return Away*Home 

def oddstoPayout(odds,dollarsIn):
  if odds<0:
    multiplier = 1/(abs(odds/100))
    return dollarsIn + dollarsIn*multiplier
  else:
    multiplier = odds/100
    return dollarsIn + dollarsIn*multiplier

def expectedValue(payout,probability):
  return payout*probability

def bet(expectedValue,Team):
  if expectedValue>1:
    return Team
  else:
    return None

def Kelly(oddsDecimal, probability):
  return (oddsDecimal*probability - (1-probability))/oddsDecimal

def teamReconstruction(id,LogTable):
  LogTableH = LogTable[LogTable.Home ==id][['gameDate','HomeGoals']]
  LogTableA = LogTable[LogTable.Away ==id][['gameDate','AwayGoals']]
  #print(LogTableH.HomeGoals.values, LogTableA.AwayGoals.values)
  mergedGoals = list(LogTableH.HomeGoals.values) + list(LogTableA.AwayGoals.values)
  mergedGames = list(LogTableH.gameDate.values) + list(LogTableA.gameDate.values)
  #print(mergedGoals,mergedGames)
  goalsScoredNew = pd.DataFrame({'Date':mergedGames, 'Goals':mergedGoals}).sort_values('Date',ascending=True).replace(np.NaN,0)
  #LogTables = pd.concat([LogTableH, LogTableA],ignore_index=True).drop_duplicates().sort_values('gameDate',ascending=False).replace(np.NaN,0)
  goalScored = [int(i) for i in np.array(goalsScoredNew.Goals)]
  return np.array(goalScored)

def teamLookBackGoals(lookupTable,lookbackDays):
  Table = []
  #print(lookbackDays)
  lookBack = df_of_the_day(lookbackDays)
  #print(lookupTable.ID.values)
  for i in lookupTable.ID.values:
    try:
      arrays = teamReconstruction(i,lookBack)
      avGoals = exponentialGoalAvWeighted(arrays)
      Table += [[i,avGoals,arrays]]
    except:
      continue
  
  Today = pd.DataFrame(Table)
  Today.columns = ['ID','avGoals','Goal Lookback']
  #print(Today)
  return Today

def exponentialGoalAvWeighted(goalsArray):
  exponential = [math.exp(-i/5) for i in range(len(goalsArray))]
  return np.average(np.array(goalsArray),weights=exponential)
  
#odds to game transformation
def identify(i,teamID= fetchName()):
  if i != 'Tie':
    return teamID[teamID.id == i.lower()].id.values[0]
  else:
    return 'Tie'

def betFunction(game, betName,parameterArray, GoalsLookup):
  #this is basically a massive switch case
  if betName == '60 Minute Line':
    gameName, Team, oddsDec = game, parameterArray[0], parameterArray[1]
    return [gameName, identify(Team), oddsDec, '60E']
  elif betName == 'Money Line':
    gameName, Team, oddsDec = game, parameterArray[0], parameterArray[1]
    return [gameName, identify(Team), oddsDec, 'ML']
  elif betName == 'Both Teams to Score':
    gameName, Result, oddsDec = game, parameterArray[0], parameterArray[1]
    #print('BTTS param array', parameterArray[0], parameterArray[1])
    return [gameName, Result, oddsDec, 'BTTS']
  else:
    return [np.NaN, np.NaN, np.NaN, np.NaN]

def getavGoals(GoalsLookup, TeamName):
	if TeamName != 'Tie':
		return (GoalsLookup[GoalsLookup.id == TeamName][['avGoals']].values[0])[0]
	else: 
		return None

def winner60(matrix, homeaway):
  if homeaway == "home":
    return np.sum(np.triu(matrix,1))
  elif homeaway == "away":
    return np.sum(np.tril(matrix,-1))
  else:
    return np.sum(np.diagonal(matrix))

def betDecisionAfter60(avGoalsHome,avGoalsAway,odds,bet):
  matrix = poissonMatrix(avGoalsHome,avGoalsAway)
  payouts = [bet+i for i in odds] #look on fanduel you will see it needs to be additive not multiplicative - this is somewhere in the odds pulling but its not an issue
  probs = [winner60(matrix,i) for i in ['home','tie','away']]
  #print(payouts, probs)
  kelly = [Kelly(payouts[i],probs[i]) for i in range(len(probs))]
  decisions = [payouts[i]*probs[i] for i in range(len(payouts))]
  #print(len(payouts), len(probs))
  placed = []
  for i in decisions:
  	if i>1.0:
  		placed += [decisions.index(i),kelly[decisions.index(i)],(probs[decisions.index(i)]-1/payouts[decisions.index(i)]),payouts[decisions.index(i)]]
  	else:
  		continue
  return placed 

def winnerOneOT(matrix,homeoraway,avGoalsHome,avGoalsAway):
  if homeoraway == 'home':
    reg = np.sum(np.triu(matrix,1).ravel())
    win = reg + (np.sum(np.diagonal(matrix)))*(avGoalsHome/(avGoalsHome+avGoalsAway)) # do lambda/lambda+lambda
    return win
  if homeoraway == 'away':
    reg = np.sum(np.tril(matrix,-1).ravel())
    win = reg + (np.sum(np.diagonal(matrix)))*(avGoalsAway/(avGoalsHome+avGoalsAway))
    return win

def betDecisionMoneylineOT(avGoalsHome,avGoalsAway,odds,bet):
  matrix = poissonMatrix(avGoalsHome,avGoalsAway)
  payouts = [bet+i for i in odds] #look on fanduel you will see it needs to be additive not multiplicative - this is somewhere in the odds pulling but its not an issue
  probs = [winnerOneOT(matrix,i,avGoalsHome,avGoalsAway) for i in ['home','away']]
  kelly = [Kelly(payouts[i],probs[i]) for i in range(len(probs))]
  decisions = [payouts[i]*probs[i] for i in range(len(payouts))]
  #print(probs, payouts, decisions)
  placed = []
  for i in decisions:
  	if i>1.0:
  		placed += [decisions.index(i),kelly[decisions.index(i)],(probs[decisions.index(i)]-1/payouts[decisions.index(i)]),payouts[decisions.index(i)]]
  	else:
  		continue
  return placed
  
def bothScore(matrix,homeoraway,avGoalsHome,avGoalsAway):
  if homeoraway == 'Yes':
  	reg = 1 - (np.sum(matrix[0,1:]) + np.sum(matrix[1:,0]) + matrix[0,0])
  	return reg
  if homeoraway == 'No':
    reg = (np.sum(matrix[0,1:]) + np.sum(matrix[1:,0]) + matrix[0,0])
    return reg 
     
def betDecisionBothScore(avGoalsHome,avGoalsAway,odds,bet):
  matrix = poissonMatrix(avGoalsHome,avGoalsAway)
  payouts = [bet+i for i in odds] #look on fanduel you will see it needs to be additive not multiplicative - this is somewhere in the odds pulling but its not an issue
  probs = [bothScore(matrix,i,avGoalsHome,avGoalsAway) for i in ['Yes','No']]
  kelly = [Kelly(payouts[i],probs[i]) for i in range(len(probs))]
  decisions = [payouts[i]*probs[i] for i in range(len(payouts))]
  #print(probs, payouts, decisions)
  placed = []
  for i in decisions:
  	if i>1.0:
  		placed += [[decisions.index(i),kelly[decisions.index(i)],(probs[decisions.index(i)]-1/payouts[decisions.index(i)]),payouts[decisions.index(i)]]]
  	else:
  		continue
  #print(placed) you need to figure out hwo to show both
  return placed

def betSwitchImplement(types, dfbig):
	if types == '60E':
		yayray = []
		for i in range(int(len(dfbig.Teams.values)/3)):
			df = dfbig[int(i*3):int(i*3+3)]
			#print(betDecisionAfter60(df.Goals.values[0],df.Goals.values[2],df.Odds.values,bet=1))
			try:
				#print(betDecisionAfter60(df.Goals.values[0],df.Goals.values[2],df.Odds.values,bet=1))	
				yields = betDecisionAfter60(df.Goals.values[0],df.Goals.values[2],df.Odds.values,bet=1)
				yayray.append([types, df.Teams.values[yields[0]], yields[1],yields[2],yields[3]])
			except:
				#print(yields)
				yayray.append([types,np.NaN,np.NaN,np.NaN,np.NaN])
		#print(yayray)
		return yayray
		
	elif types =='ML':
		yayray = []
		for i in range(int(len(dfbig.Teams.values)/2)):
			df = dfbig[int(i*2):int(i*2+2)]
			try:
				yields = betDecisionMoneylineOT(df.Goals.values[0],df.Goals.values[1],df.Odds.values,bet=1)
				yayray.append([types, df.Teams.values[yields[0]], yields[1],yields[2],yields[3]])
			except:
				#print(yields)
				yayray.append([types,np.NaN,np.NaN,np.NaN,np.NaN])
		#print(yayray)
		return yayray
	elif types =='BTTS':
		try:
			yields = betDecisionBothScore(df.Goals.values[0],df.Goals.values[1],df.Odds.values,bet=1)
			return [types, df.Result.values[yields[0]], yields[1],yields[2],yields[3]]
		except:
			return [types, np.NaN,np.NaN,np.NaN,np.NaN]

def identifyName(temp,toggle):
	if toggle == 'away':
		return temp.Game.values[0].split('At')[0][0:-1]
	elif toggle == 'home':
		return temp.Game.values[0].split('At')[1][1:]

def placeBet(temp, GoalsLookup):
	if temp.Type.values[0] =='BTTS':
		types = temp.Type.values[0]
		Result = temp.Team.values
		Odds = temp.DecimalOdds.values
		Teams = [identifyName(temp,'away'), identifyName(temp,'home')]
		avGoals = [getavGoals(GoalsLookup, identify(i)) for i in Teams]
		goalDf = pd.DataFrame({'Result':Result, 'Goals':avGoals, 'Odds':Odds})
		bets = betSwitchImplement(types, goalDf)
		return bets
		
	else:
		types = temp.Type.values[0]
		Teams = temp.Team.values
		Odds = temp.DecimalOdds.values
		avGoals = [getavGoals(GoalsLookup, i) for i in Teams]
		goalDf = pd.DataFrame({'Teams':Teams, 'Goals':avGoals, 'Odds':Odds})
		bets = betSwitchImplement(types, goalDf)
		#print(bets)
		return bets

def dailyBetParse(oddsDataFrame,GoalsLookup):
	placedBet = []
	for i in np.unique(oddsDataFrame.Type.values):
		temp = oddsDataFrame[oddsDataFrame.Type == i]
		here = placeBet(temp,GoalsLookup)
		for i in here:
			placedBet += [i]
	BetFrame = pd.DataFrame(placedBet)
	BetFrame = BetFrame.dropna()
	BetFrame.columns = ['Bet Type','Bet State Chosen', 'Kelly Criterion Suggestion', 'Probability Spread','Payouts (per Dollar)']
	return BetFrame
	
def powerLaw(portfolioAmt,df):
  probs = np.array([(1-(1/i)) for i in df['Payouts (per Dollar)'].values]) #can be used for higher risk tolerance though unused here
  amount = 1/np.prod(probs) #test portfolio constraints
  kelly = df['Kelly Criterion Suggestion'].values
  spread = df['Probability Spread'].values
  allocation1 = [np.minimum((portfolioAmt*i)*(i/np.sum(kelly)), 0.3*portfolioAmt) for i in kelly] #RISK TOLERANCE ESTABLISHED HERE 
  df['Allocation Dollars'] = allocation1
  print('Total Allocated', np.sum(allocation1), 'out of', portfolioAmt)
  df['Allocation Percentage'] = [(i/portfolioAmt) for i in allocation1]
  return df

def gainsLosses(allocation,successes, df, portfolio):
  payouts = df['Payouts (per Dollar)'].values
  prev = np.sum(allocation)
  now = np.sum(np.dot([allocation[i]*payouts[i] for i in range(len(payouts))], successes))
  return [portfolio+(now-prev), prev, now]

def picks(): #this needs some work/checking
	result = fetch().round(decimals=2)
	resulting = result[['Bet State Chosen', 'Kelly Criterion Suggestion','Payouts (per Dollar)']]
	resulting['League'] = ['ELO']*len(resulting['Bet State Chosen'])
	resulting['Date'] = [str(date.today())]*len(resulting['Bet State Chosen'])
	resulting.to_csv(os.getcwd() + '/masterDaily.csv', mode='a', header=False)
	return 'ELO Done'

def searchingForGame(jsonData):
	results_df = pd.DataFrame()
	alpha = jsonData['events'][0]
	gameday = alpha['tsstart'][:10]
	today = str(date.today())
	#print(today, gameday)
	return today == gameday

def gameToday():
	jsonData_fanduel_epl = requests.get('https://sportsbook.fanduel.com/cache/psmg/UK/63782.3.json').json()
	boolean = searchingForGame(jsonData_fanduel_epl)
	return boolean

'''
To do:
-- comment some more stuff and figure out hwo to implement NHl in this exact framework, maybe jsut replace the XHR, but the bettting is different, run seperately?
-- add over under, period bets, make the names for tie more clear if possible
-- make tree structure easy to implement

Notes:
-- this will force people to make a directory or maybe to have a folder called data in place, thinking of possible easy of application

Watchouts:
-- XHR can be faulty, give it a check in function fetch()
'''
#makes on function and add success failiure when looking up the result

def picks():
	print('Just wait a moment while we retreive todays teams, odds, and historical data.')
	oddsDataFrame = fetch()
	time.sleep(15)
	teamID = fetchName()
	GoalsLookup = pd.merge(fetchName(), teamLookBackGoals(teamID,21), on='ID')
	Daily = dailyBetParse(oddsDataFrame,GoalsLookup)
	result = Daily.round(decimals=2)
	results = result[result['Bet Type'] == 'ML']
	print(results.to_markdown())
	resulting = results[['Bet State Chosen', 'Kelly Criterion Suggestion','Payouts (per Dollar)']]
	resulting['League'] = ['KHL']*len(resulting['Bet State Chosen'])
	resulting['Date'] = [str(date.today())]*len(resulting['Bet State Chosen'])
	resulting.to_csv(os.getcwd() + '/masterDaily.csv', mode='a', header=False)
	return 'KHL Done'

def run():
	if gameToday():
		return picks()
	else:
		return ('No KHL games today.')

print(run())
	
