import time,csv,sys
from pytz import timezone
from datetime import datetime
import pandas
from pandas import read_csv

sys.path.append('../utils')
import mtaUpdates

# This script should be run seperately before we start using the application
# Purpose of this script is to gather enough data to build a training model for Amazon machine learning
# Each time you run the script it gathers data from the feed and writes to a file
# You can specify how many iterations you want the code to run. Default is 50
# This program only collects data. Sometimes you get multiple entries for the same tripId. we can timestamp the
# entry so that when we clean up data we use the latest entry

# Change DAY to the day given in the feed
DAY = datetime.today().strftime("%A")
TIMEZONE = timezone('America/New_York')

global ITERATIONS
global WD
global COOLTIME
ITERATIONS = 10
COOLTIME = 0
WD = 'Weekday'

#################################################################
####### Note you MAY add more datafields if you see fit #########
#################################################################

# column headers for the csv file
columns = ['timestamp','tripId','route','day','timeToReachSource','timeToReachExpressStation','timeToReachDestination']


def main(fileName):
    """
    Run function 'adding',
    Then remove the duplicate data based on tripId.
    Finally, Append remaining entries to .csv file.
    """
    # API key
    with open('../utils/api_key.txt', 'rb') as keyfile:
        APIKEY = keyfile.read().rstrip('\n')
        keyfile.close()

	### INSERT YOUR CODE HERE ###
    tripUpdates = mtaUpdates.mtaUpdates(APIKEY)

    with open(fileName, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile,delimiter=',')
        csvwriter.writerow(columns)  # Write first row in .csv file
        csvfile.close()
    if (DAY=="Saturday" or DAY=="Sunday"):
        WD = 'Weekend'

    try:
        while(1):
            rawData = adding(tripUpdates)
            # Preliminary Cleaning: remove duplicate entries based on tripId
            data = rawData.groupby('tripId').apply(lambda x: x.ix[x.timestamp.idxmax()])
            # Append entries to .csv file
            data.to_csv(fileName, mode='ab', header=False, index=False)

    except KeyboardInterrupt:
        exit


def adding(tripUpdates):
    """
    Fetch data from MTA feed ITERATION times in a row.
    Sleep time between two fetches is COOLTIME.
    Input: a tripUpdates object
    Return: a pandas.DataFrame object
    """
    rawData = pandas.DataFrame(columns=('timestamp','tripId','route','day','timeToReachSource','timeToReachExpressStation','timeToReachDestination'))
    update_list = tripUpdates.getTripUpdates()
    for i in range (ITERATIONS):
        for t in update_list:
            time.sleep(COOLTIME)
            # Write new data to csv
            if (t['routeId']=="1"):
                 # check if the selected train1 has arrival time data for 110th, 96th, 42ns street
                if('117S' in t['futureStopData'].keys()
                   and '120S' in t['futureStopData'].keys()
                   and '127S' in t['futureStopData'].keys()):
                    if('arrivalTime' in t['futureStopData']['117S'][0]
                       and 'arrivalTime' in t['futureStopData']['120S'][0]
                       and 'arrivalTime' in t['futureStopData']['127S'][0]):
                        if(t['futureStopData']['117S'][0]['arrivalTime']!=0
                           and t['futureStopData']['120S'][0]['arrivalTime']!=0
                           and t['futureStopData']['127S'][0]['arrivalTime']!=0):
                           # Passed validity check. Append data to rawData.   ###t['tripId'][0:5]###
                           data = [t['timeStamp'], t['tripId'], t['routeId'],WD,
                                    t['futureStopData']['117S'][0]['arrivalTime'],
                                    t['futureStopData']['120S'][0]['arrivalTime'],
                                    t['futureStopData']['127S'][0]['arrivalTime']]
                           columns=['timestamp','tripId','route','day','timeToReachSource','timeToReachExpressStation','timeToReachDestination']
                           row = dict()
                           for i in range(7):
                                row[columns[i]] = data[i]
                           # print "line 1 row:", row
                           rawData = rawData.append(row, ignore_index=True)

            if (t['routeId']=="2" or t['routeId']=="3"):
                # check if the selected train 2 or 3 has arrival time data for 96th, 42ns street
                if('120S' in t['futureStopData'].keys() and '127S' in t['futureStopData'].keys()):
                    if('arrivalTime' in t['futureStopData']['120S'][0]
                       and 'arrivalTime' in t['futureStopData']['127S'][0]):
                        if(t['futureStopData']['120S'][0]['arrivalTime']!=0
                             and t['futureStopData']['127S'][0]['arrivalTime']!=0):
                            # Passed validity check. Append data to rawData.
                            data = [t['timeStamp'], t['tripId'], t['routeId'],WD,'0',
                                    t['futureStopData']['120S'][0]['arrivalTime'],
                                    t['futureStopData']['127S'][0]['arrivalTime']]
                            columns=['timestamp','tripId','route','day','timeToReachSource','timeToReachExpressStation','timeToReachDestination']
                            row = dict()
                            for i in range(7):
                                row[columns[i]] = data[i]
                            rawData = rawData.append(row, ignore_index=True)

    return rawData
    ### CODE ENDS ###

if __name__ == "__main__":
    main( 'data.csv')
