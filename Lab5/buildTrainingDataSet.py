## This program is used to clean out the data from the csv that you collected.
## It aims at removing duplicate entries and extracting any further insights
## that the author(s) of the code may see fit

## Usage (for file as is currently): python buildTrainingDataSet.py <filename of file from part 1>

import sys

# Pandas is a python library used for data analysis
import pandas
from pandas import read_csv
from pytz import timezone
from datetime import datetime


TIMEZONE = timezone('America/New_York')


def main(fileHandle):
	# This creates a dataframe
	rawData = read_csv(fileHandle)

	# Remove duplicate entries based on tripId, retain the one with maximum timestamp
	data = rawData.groupby('tripId').apply(lambda x: x.ix[x.timestamp.idxmax()])

	# Seperate all the local trains and form a new data frame
	localTrains = data[data.route == '1']

	# Express trains
	#expressTrains = data[data.route == 'E']

    # Line 2 & Line 3 trains
    line2Trains = data[data.route == '2']
    line3Trains = data[data.route == '3']

	# 1. Find the time difference (to reach 96th) between all combinations of local trains and express #####
	# 2. Consider only positive delta
	# 3. Make the final table
    # 4. Upload the final table to Amazon S3

	# Create a new data frame for final table
	finalData = pandas.DataFrame(columns=('arrive116Time', 'Wkdy/Wknd', 'Recommendation'))

	############## INSERT YOUR CODE HERE ###############
    idx = 0  # row index for finalData

    # Check data's validity, remove invalid rows
    localTrains = localTrains[lcoalTrains.arrive116Time and localTrains.arrive96Time and localTrains.arrive42Time]
    localTrains = localTrains[lcoalTrains.arrive116Time < localTrains.arrive96Time < localTrains.arrive42Time]

    line2Trains = line2Trains[line2Trains.arrive96Time and line2Trains.arrive42Time]
    line2Trains = line2Trains[line2Trains.arrive96Time < line2Trains.arrive42Time]

    line3Trains = line3Trains[line3Trains.arrive96Time and line3Trains.arrive42Time]
    line3Trains = line3Trains[line3Trains.arrive96Time < line3Trains.arrive42Time]

    # For Each Line 1 train arriving 116th Street,
    # compute whether "SWITCH" or "STAY" at 96th Street
    for index, line1Row in localTrains.iterrows():
        line1Arrive116Time = line1Row['arrive116Time']
        line1Arrive96Time = line1Row['arrive96Time']
        line1Arrive42Time = line1Row['arrive42Time']

        try:
            line2Available = line2Trains[line2Trains.arrive96Time > line1Arrive96Time]
            line2Arrive42Time = line2Available['arrive42Time'].min()
        # There could be cases where line 1 train cannot find it's matching Line 2 train
        except IndexError:
            line2Arrive42Time = 9999999999 # No applicable Line 2 Trains

        try:
            line3Available = line3Trains[line3Trains.arrive96Time > line1Arrive96Time]
            lin3Arrive42Time = line3Available['arrive42Time'].min()
        except IndexError:
            line3Arrive42Time = 9999999999 # No applicable Line 3 Trains

        # Based on "delta", choose whether to 'SWITCH' or 'STAY'
        if line1Arrive42Time <= line2Arrive42Time and line1Arrive42Time <= line3Arrive42Time:
            recom = 'STAY'
        elif line2Arrive42Time <= line1Arrive42Time and line2Arrive42Time <= line3Arrive42Time:
            recom = 'SWITCH TO LINE 2'
        else:
            recom = 'SWITCH TO LINE 3'

        finalData.loc[idx] = [line1Arrive116Time, line1Row['dow'], recom]
        idx += 1

    ############## END OF CODE ####################

	finalData.to_csv("finalData.csv",index=False)



if __name__ == "__main__":

	lengthArg = len(sys.argv)


	if lengthArg < 2:
		print "Missing arguments"
		sys.exit(-1)

	if lengthArg > 2:
		print "Extra arguments"
		sys.exit(-1)

	fileHandle = sys.argv[1]
	main(fileHandle)
