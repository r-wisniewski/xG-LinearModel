"""
Usage: python ahl_scraper.py [start game ID] [last game ID] [output csv name]

Scrape all shot and goal events (from start game to last game) and export as a csv for import by the linear model.
"""

import requests
import json
import sys
import numpy as np
import pandas as pd

# take in cmd line args
first_game_id = int(sys.argv[1])
last_game = int(sys.argv[2])
filename = str(sys.argv[3]) + '.csv'

#callbacks._8 includes all the shot/goal data including x,y coordinates etc...
url = 'https://lscluster.hockeytech.com/feed/index.php?feed=statviewfeed&view=gameCenterPlayByPlay&game_id='
end ='&key=50c2cd9b5e18e390&client_code=ahl&lang=en&league_id=&callback=angular.callbacks._8'

# Define a pandas dataframe to store the scraped data
xg_df = pd.DataFrame(columns=['XLocation', 'YLocation', 'Strength', 'Goal'])

for n in range(first_game_id,last_game+1,1):
    ######### Loop through the game summaries ###########
    
    fullurl = url + str(n) + end
    
    resp = requests.get(fullurl)
        
    #format resp and resp2 to be json responses. Cut the beginning and end portions off
    resp = resp.text[:-1]
    resp = resp[21:]
    #this response is json
    try:
        resp = json.loads(resp)

        resp1 = resp
        resp2 = resp

        #Team1 is the team that the strengths will be calculated for
        #Team2 is just the inverse of Team1
        #ie, if Team1 is on the PP (strength = +1), Team2 must have the inverse strength == -1 (5v4 PK)
        team = []
        for i in resp:
            event = i.get("event")
            if event == "goalie_change":
                details = i.get("details")
                team_id = details.get("team_id")
                team.append(team_id) 
        Team1 = int(team[0])
        Team2 = int(team[1])

        # Create and populate array with strengths
        # 3 20 min periods plus possible 5 min OT (for regular season) = 65 min * 60 secs = 3900 secs
        # gametime == [0,1,2.......,3899]
        gametime = np.arange(0,3900)
        zero_array = np.zeros(3900)
        #combine arrays into a 2D array where a row is the time combined with the strength at that moment 
        #in time (for Team1)
        # Access as: strengths[row,col]
        strengths = np.vstack((gametime, zero_array)).T

        # First run through the events, we create and populate the strength array
        # Strengths are calculated as the advantage or disadvantage of Team 1
        # ie, +1 can indicate 5v4 OR 4v3 in favor of Team1
        for i in resp1:
            #get the event type and assume we have all metadata
            event = i.get("event")

            ######### calculate strengths at each moment in time ########

            #keep the time of (the last penalty + penalty length) 
            last_penalty_time = 0

            if event == "penalty":
                details = i.get("details")
                time_raw = details.get("time").split(":")
                period = details.get("period")
                period = int(period.get("id"))
                #get time in seconds of the penalty
                time = ((period-1) * 20 * 60) + (int(time_raw[0]) * 60) + int(time_raw[1])
                length = details.get("minutes").split(".")
                length = int(length[0])

                against_team = details.get("againstTeam")
                against_team = against_team.get("id")
                against_team = int(against_team)
                #Team1 goes on the PP
                if against_team == Team2:
                    if length == 2:
                        last_penalty_time = time + 120
                        #set the strength 
                        for i in range(121):
                            if int(strengths[time+i,1]) < 2:
                                strengths[time+i,1] += 1
                    if length == 5:
                        last_penalty_time = time + 300
                        for i in range(301):
                            if int(strengths[time+i,1]) < 2:
                                strengths[time+i,1] += 1
                
                #Team1 goes on the PK
                elif against_team == Team1:
                    if length == 2:
                        last_penalty_time = time + 120
                        #set the strength 
                        for i in range(121):
                            if int(strengths[time+i,1]) > -2:
                                strengths[time+i,1] -= 1
                    if length == 5:
                        last_penalty_time = time + 300
                        for i in range(301):
                            if int(strengths[time+i,1]) > -2:
                                strengths[time+i,1] -= 1

            #we only care about PP goals becuase SH or EV goals don't change strength
            elif event == "goal":
                details = i.get("details")
                pp_goal = details.get("properties")
                pp_goal = int(pp_goal.get("isPowerPlay"))
                team_id = details.get("team")
                team_id = int(team_id.get("id"))
                if pp_goal == 1:
                    #time of goal in seconds
                    time_raw = details.get("time").split(":")
                    period = details.get("period")
                    period = int(period.get("id"))
                    time_of_goal = ((period-1) * 20 * 60) + (int(time_raw[0]) * 60) + int(time_raw[1])

                    #time of previous penalty + length of penalty is last_penalty_time
                    #remove the additional "strengths" after a PP goal is scored
                    #ie, if Team1 goes on the PP at 10:00 and the PP goal is scored at 8:50, then remove
                    #the additional +1 strengths from 8:51 to 8:00
                    if team_id == Team1:
                        for i in range(time_of_goal+1,last_penalty_time+1):
                            if int(strengths[i,1]) > -2:
                                strengths[i,1] -= 1

                    elif team_id == Team2:
                        for i in range(time_of_goal+1,last_penalty_time+1):
                            if int(strengths[i,1]) < 2:
                                strengths[i,1] += 1

        # 2nd run through the events, we get the goal and combine that with strength.
        for i in resp2:
            #get the event type and assume we have all metadata
            event = i.get("event")
            if event == "shot" or event == "goal":
                details = i.get("details")

                #set the X value relative to x distance from the net
                # this is because the home team's x value is (max X)/2 + true X
                # max x = 593/2
                # X value is out towards the blue line
                xLocation = details.get("xLocation")
                if xLocation > 593/2:
                    xLocation = 593 - xLocation
                else:
                    pass
                #get the Y value as a Y distance relative to the net
                #largest Y val is 300.
                #since origin is at top left we must flip all the y values
                yLocation = details.get("yLocation")
                yLocation = 300 - yLocation
                isGoal = details.get("isGoal")

                #get the team id of the shooter
                if event == "goal":
                    team_id = details.get("team")
                    team_id = int(team_id.get("id"))
                elif event == "shot":
                    team_id = int(details.get("shooterTeamId"))

                #get time of goal or shot and match to strength
                time_raw = details.get("time").split(":")
                period = details.get("period")
                period = int(period.get("id"))
                event_time = ((period-1) * 20 * 60) + (int(time_raw[0]) * 60) + int(time_raw[1])

                #if the team who shot on net or scored is Team1, set strength equal to the strength array 
                #if the team who shot on net or scored is Team1, set strength to the inverse of the strength array
                if team_id == Team1:
                    event_strength = strengths[event_time,1]
                    event_strength = int(event_strength)
                else:
                    event_strength = strengths[event_time,1]
                    event_strength = -int(event_strength)

                #only append a row if the scraper got a 0 or 1 for whether or not this event was a goal. Omit nulls.
                if isGoal ==0 or isGoal == 1:
                    #add new row to the training pandas dataframe
                    new_row = [xLocation, yLocation, event_strength, isGoal]
                    r_series = pd.Series(new_row,index=xg_df.columns)
                    xg_df = xg_df.append(r_series, ignore_index=True)
                    
        #print game ID to see current progress
        print("Game ID: %i" % n)
    except:
        pass

#export pandas dataframe to csv using passed filename
xg_df.to_csv(filename,index=False)