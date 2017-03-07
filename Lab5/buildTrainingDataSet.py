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


def pts(time):
    """
	pts: POSIX TO SECONDS
    Convert POSIX time format to human-readable format.
    "YYYY-MM-DD HH:MM:SS"
    """

    hms = str(datetime.fromtimestamp(time, timezone('America/New_York')))[11:19]
    seconds = int(hms.split(':')[0]) * 3600 + int(hms.split(':')[1]) * 60 + int(hms.split(':')[2])
    return seconds


def gencdv(fileHandle, w_a, c_r):
	# This creates a dataframe
	rawData = read_csv(fileHandle)

	# Remove duplicate entries based on tripId, retain the one with maximum timestamp
	data = rawData.groupby('tripId').apply(lambda x: x.ix[x.timestamp.idxmax()])

	# Seperate all the local trains and form a new data frame
	localTrains = data[data.route == 1]

	# Express trains
	#expressTrains = data[data.route == 'E']

    # Line 2 & Line 3 trains
	line2Trains = data[data.route == 2]
	line3Trains = data[data.route == 3]

	# 1. Find the time difference (to reach 96th) between all combinations of local trains and express #####
	# 2. Consider only positive delta
	# 3. Make the final table
    # 4. Upload the final table to Amazon S3

	# Create a new data frame for final table
	#### CLASSIFICATION
	if c_r == 'c':
		finalData = pandas.DataFrame(columns=('timestamp','Wkdy/Wknd','arrive116Time','arrive96Time','arrive42Time','Recommendation'))
	#### REGRESSION
	else:
		finalData = pandas.DataFrame(columns=('Wkdy/Wknd','arrive116Time','Line1Cost','Line2Cost','Line3Cost'))

	############## INSERT YOUR CODE HERE ###############
	idx = 0  # row index for finalData

    # Check data's validity, remove invalid rows
	localTrains = localTrains[localTrains.timeToReachSource < localTrains.timeToReachExpressStation]
	localTrains = localTrains[localTrains.timeToReachExpressStation < localTrains.timeToReachDestination]
	line2Trains = line2Trains[line2Trains.timeToReachExpressStation < line2Trains.timeToReachDestination]
	line3Trains = line3Trains[line3Trains.timeToReachExpressStation < line3Trains.timeToReachDestination]

	# For Each Line 1 train arriving 116th Street,
	# compute whether "SWITCH" or "STAY" at 96th Street
	for index, line1Row in localTrains.iterrows():
		# Extract each entry's attributes in data.csv
		timestamp = pts(line1Row['timestamp'])
		# Weekday --> 1; Weekend --> 0
		if line1Row['day'] == 'Weekday':
			wdwe = 1
		else:
			wdwe = 0

		line1Arrive116Time = pts(line1Row['timeToReachSource'])
		line1Arrive96Time = pts(line1Row['timeToReachExpressStation'])
		line1Arrive42Time = pts(line1Row['timeToReachDestination'])

		# Time duration
		line1Td = line1Arrive42Time - line1Arrive116Time
		try:
			line2Available = line2Trains[line2Trains.timeToReachExpressStation > line1Row['timeToReachExpressStation']]
			line2Arrive42Time = pts(line2Available['timeToReachDestination'].min())
			line2Td = line2Arrive42Time - line1Arrive116Time
		# There could be cases where line 1 train cannot find it's matching Line 2 train
		except (IndexError, ValueError) as e:
			continue
		    # line2Arrive42Time = 9999999999 # No applicable Line 2 Trains

		try:
			line3Available = line3Trains[line3Trains.timeToReachExpressStation > line1Row['timeToReachExpressStation']]
			line3Arrive42Time = pts(line3Available['timeToReachDestination'].min())
			line3Td = line3Arrive42Time - line1Arrive116Time
		except (IndexError, ValueError) as e:
			continue
		    # line3Arrive42Time = 9999999999 # No applicable Line 3 Trains

		#### CLASSIFICATION
		# Based on "delta", choose whether to 'SWITCH' or 'STAY'
		if line1Arrive42Time <= line2Arrive42Time and line1Arrive42Time <= line3Arrive42Time:
		    recom = 1  # Stay on line 1
		elif line2Arrive42Time <= line1Arrive42Time and line2Arrive42Time <= line3Arrive42Time:
		    recom = 2  # Switch to line 2
		else:
		    recom = 3  # Switch to line 3

		if recom == 2 or recom == 3:
			recom = 0  # Switch

		#### CLASSIFICATION
		if c_r == 'c':
			## columns=('timestamp','Wkdy/Wknd', 'arrive116Time', 'arrive96Time', 'arrive42Time','Recommendation')
			finalData.loc[idx] = [timestamp, wdwe, line1Arrive116Time, line1Arrive96Time, line1Arrive42Time, recom]
		#### REGRESSION
		else:
			## columns=('Wkdy/Wknd','arrive116Time','Line1Cost','Line2Cost','Line3Cost')
			finalData.loc[idx] = [wdwe, line1Arrive116Time, line1Td, line2Td, line3Td]

		idx += 1

	############## END OF CODE ####################
	# Write new .csv file or append existing file
	if w_a == 'a':
		finalData.to_csv("finalData.csv", mode='ab', header=False, index=False)
	else:
		finalData.to_csv("finalData.csv", mode='w', index=False)


def main(fh1, fh2, fh3, fh4, fh5, c_r):
	fh_list = [fh1, fh2, fh3, fh4, fh5]
	for fh in fh_list:
		if fh == fh_list[0]:
			gencdv(fh, w_a='w', c_r=c_r)
		else:
			gencdv(fh, w_a='a', c_r=c_r)



if __name__ == "__main__":

	lengthArg = len(sys.argv)


	if lengthArg < 7:
		print "Missing arguments"
		sys.exit(-1)

	if lengthArg > 7:
		print "Extra arguments"
		sys.exit(-1)

	fileHandle1 = sys.argv[1]
	fileHandle2 = sys.argv[2]
	fileHandle3 = sys.argv[3]
	fileHandle4 = sys.argv[4]
	fileHandle5 = sys.argv[5]
	c_r = sys.argv[6]
	main(fileHandle1, fileHandle2, fileHandle3, fileHandle4, fileHandle5, c_r)
