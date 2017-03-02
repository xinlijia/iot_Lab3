import time,csv,sys
from pytz import timezone
from datetime import datetime

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
#Default number of iterations
ITERATIONS = 1
WD = 'Weekday'



#################################################################
####### Note you MAY add more datafields if you see fit #########
#################################################################

# column headers for the csv file
columns =['timestamp','tripId','route','day','timeToReachExpressStation','timeToReachDestination']


def main(fileName):
    # API key
    with open('key.txt', 'rb') as keyfile:
        APIKEY = keyfile.read().rstrip('\n')
        keyfile.close()

	### INSERT YOUR CODE HERE ###
    tripUpdates = mtaUpdates.mtaUpdates(APIKEY)
    with open(fileName, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile,delimiter=',')
        csvwriter.writerow(['Timestamp','tripId/train start time','Route','Day of the week',
                            'Time at which it reaches express station (at 116th street)',
                            'Time at which it reaches express station (at 96th street)',
                            'Time at which it reaches the destination (at 42nd Street)'])
        csvfile.close()

    if (DAY=="Saturday" or DAY=="Sunday"):
        WD = 'Weekend'
    try:
        while(1):
            adding(fileName, tripUpdates)   
    except KeyboardInterrupt:
        exit 
def adding(fileName, tripUpdates):
    # Get data from feed
    update_list = tripUpdates.getTripUpdates()
    for t in update_list:
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
                        with open(fileName, 'ab') as csvfile:
                            csvwriter = csv.writer(csvfile,delimiter=',')
                            csvwriter.writerow([t['timeStamp'], t['tripId'][0:5], t['routeId'],WD,
                                                t['futureStopData']['117S'][0]['arrivalTime'],
                                                 t['futureStopData']['120S'][0]['arrivalTime'],
                                                 t['futureStopData']['127S'][0]['arrivalTime']]) 
                            csvfile.close()
        if (t['routeId']=="2" or t['routeId']=="3"):
             # check if the selected train 2 or 3 has arrival time data for 96th, 42ns street
            if('120S' in t['futureStopData'].keys() and '127S' in t['futureStopData'].keys()):
                if('arrivalTime' in t['futureStopData']['120S'][0] 
                   and 'arrivalTime' in t['futureStopData']['127S'][0]):
                    if(t['futureStopData']['120S'][0]['arrivalTime']!=0 
                         and t['futureStopData']['127S'][0]['arrivalTime']!=0):
                        with open(fileName, 'ab') as csvfile:
                            csvwriter = csv.writer(csvfile,delimiter=',')
                            csvwriter.writerow([t['timeStamp'], t['tripId'][0:5], t['routeId'],WD,'0',
                                                 t['futureStopData']['120S'][0]['arrivalTime'],
                                                 t['futureStopData']['127S'][0]['arrivalTime']])  
                            csvfile.close()

if __name__ == "__main__":
    main( 'test.csv')
