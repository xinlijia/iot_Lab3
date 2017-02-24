# *********************************************************************************************
# Usage python mta.py

import json,time,csv,sys
import boto
import boto.sns
import boto3
from boto3.dynamodb.conditions import Key,Attr
import urllib2,contextlib
from datetime import datetime
from pytz import timezone
sys.path.append('../utils/')
import gtfs_realtime_pb2, mtaUpdates
import google.protobuf
import aws

# with open('aws_connect.txt', 'rb') as aws_file:
#    content = aws_file.readlines()
#    ACCOUNT_ID = content[0].rstrip('\n').split()[2]
#    IDENTITY_POOL_ID = content[1].rstrip('\n').split()[2]
#    ROLE_ARN = content[2].rstrip('\n').split()[2]
#    aws_file.close()

# Use cognito to setup identity
# cognito = boto.connect_cognito_identity()
# cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
# oidc = cognito.get_open_id_token(cognito_id['IdentityId'])
# sts = boto.connect_sts()
# assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])

# Connect to DynamoDB
# ATTENTION: When using Edison, new table need to be authorized, see Week 3.9
# client_dynamo = boto.dynamodb2.connect_to_region(
#    'us-east-1',
#    aws_access_key_id=assumedRoleObject.credentials.access_key,
#    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
#    security_token=assumedRoleObject.credentials.session_token)

# Create New Table or use existing table.
# Trip ID as hashkey; Timestamp as RangeKey.
# from boto.dynamodb2.table import Table
# from boto.dynamodb2.fields import HashKey, RangeKey

# DYNAMODB_TABLE_NAME = "Lab3"
# ac = Table(DYNAMODB_TABLE_NAME, connection = client_dynamo)
# items = ac.scan()

def source():
    s = raw_input("Please enter your source station : ")
    station = int(s)
    while (120 < station < 127):
        print "please enter a station North of the 96th street or South of 42nd street : "
        s = input()
        station = int(s)
    return station

def dest():
    s = raw_input("Please enter your destination : ")
    station = int(s)
    while (120 < station < 127):
        print "please enter a station North of the 96th street or South of 42nd street : "
        s = input()
        station = int(s)
    return station


def readable_time(time):
    """
    Convert POSIX time format to human-readable format.
    "YYYY-MM-DD HH:MM:SS"
    """
    return str(datetime.fromtimestamp(time, timezone('America/New_York')))[0:19]

def main():
    result = ''
    while(1):
        c=source()
        d=dest()
        while ((c<120 and d<120) or (c>127 and d>127)):
            print "Please re-enter your source station and destination"
            c = source()
            d = dest()
        if (c<d):
            s = ''.join([str(c),'S'])
            d = ''.join([str(d),'S'])
            if (planTripS(s,d)== True):
                result = 'Switch'
            else:
                result = 'Stay'
            print result
        else:
            s = ''.join([str(c),'N'])
            d = ''.join([str(d),'N'])
            if (planTripN(s,d)== True):
                result = 'Switch'
            else:
                result = 'Stay'
            print result



def planTripS(source, destination):
    """
    Return: bool type, 'True'-- Switch train
    """
    # Fetch data directly from MTA feed.
    with open('../utils/api_key.txt', 'rb') as keyfile:
        key = keyfile.read().rstrip('\n')
    tripUpdates = mtaUpdates.mtaUpdates(key)
    items = tripUpdates.getTripUpdates()

    line1,line2,line3=[],[],[]
    line1_min,line2_min,line3_min=-1,-1,-1
    line1Arrival96Time = 0
    for item in items:
        if (item['routeId']=="1"):
            # check if the selected train1 has arrival time data for source
            if( source in item['futureStopData'].keys()):
                if('arrivalTime' in item['futureStopData'][source][0]):
                    if(item['futureStopData'][source][0]['arrivalTime']!=0):
                        line1.append(item)
                        if(line1_min==-1):
                            line1_i=item
                            line1_min=item['futureStopData'][source][0]['arrivalTime']
                        elif(line1_min>=item['futureStopData'][source][0]['arrivalTime']):
                            line1_i=item
                            line1_min=item['futureStopData'][source][0]['arrivalTime']

    if(line1_min==-1):
        raise Exception('line 1 data error 1')
    #check if the selected train 1 has arrival time data for 96th and 42nd
        if (line1_i['futureStopData']["120S"][0]['arrivalTime']=="0" or line1_i['futureStopData']["127S"][0]['arrivalTime']=="0" or line1_i['futureStopData'][source][0]['arrivalTime']=="0" or line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
            raise Exception('line 1 data error 2')
        else:
            line1Arrival96Time=int(line1_i['futureStopData']["120S"][0]['arrivalTime'])

    #find nearest 2,3 train, return if there's an error
    for item in items:
        #case line2
        if(item['routeId']=="2"):
            #check if train 2 has arrival time data for 96th and 42nd
            if("120S" in item['futureStopData'].keys() and "127S" in item['futureStopData'].keys()):
                if(item['futureStopData']["120S"][0]['arrivalTime']=="0" or item['futureStopData']["127S"][0]['arrivalTime']=="0"):
                    raise Exception('line 2 data error')
                elif(int(item['futureStopData']["120S"][0]['arrivalTime'])>line1Arrival96Time):
                    #line2.append(item)
                    if(line2_min==-1):
                        line2_i=item
                        line2_min=int(item['futureStopData']["120S"][0]['arrivalTime'])
                    elif(line2_min>=int(item['futureStopData']["120S"][0]['arrivalTime'])):
                        line2_i=item
                        line2_min=int(item['futureStopData']["120S"][0]['arrivalTime'])
        #case line3
        if(item['routeId']=="3"):
            #check if train 3 has arrival time data for 96th and 42nd
            if("120S" in item['futureStopData'].keys() and "127S" in item['futureStopData'].keys()):
                if(item['futureStopData']["120S"][0]['arrivalTime']=="0" or item['futureStopData']["127S"][0]['arrivalTime']=="0"):
                    raise Exception('line 3 data error')
                elif(int(item['futureStopData']["120S"][0]['arrivalTime'])>line1Arrival96Time):
                    #line3.append(item)
                    if(line3_min==-1):
                        line3_i=item
                        line3_min=int(item['futureStopData']["120S"][0]['arrivalTime'])
                    elif(line3_min>=int(item['futureStopData']["120S"][0]['arrivalTime'])):
                        line3_i=item
                        line3_min=int(item['futureStopData']["120S"][0]['arrivalTime'])

    #Compared the arrival time on 42th of three lines
    line1Arrival42Time=line1_i['futureStopData']["127S"][0]['arrivalTime']
    line2Arrival42Time=line2_i['futureStopData']["127S"][0]['arrivalTime']
    line3Arrival42Time=line3_i['futureStopData']["127S"][0]['arrivalTime']

    # check if the selected train 1 has arrival time for destination
    if (line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
        raise Exception('line 1 data error 3')
    line1ArrivalTime=line1_i['futureStopData'][destination][0]['arrivalTime']
    currentTime1 = line1_i['timeStamp']
    line1time = line1ArrivalTime - currentTime1
    print "If you stay, you will arrive at : ", readable_time(line1ArrivalTime), ", take ", line1time, "seconds"

    if(line1Arrival42Time>line2Arrival42Time or line1Arrival42Time>line3Arrival42Time):
        # If switch, when arrive at 42th, transfer to the nearest line 1
        line1_min=-1
        #If take train2
        if (line2Arrival42Time<line3Arrival42Time):
            for item in items:
                if (item['routeId']=="1"):
                    if( "127S" in item['futureStopData'].keys() and destination in item['futureStopData'].keys()):
                        if('arrivalTime' in item['futureStopData']["127S"][0] ):
                            if(item['futureStopData']["127S"][0]['arrivalTime']!=0 and item['futureStopData'][destination][0]['arrivalTime']!=0):
                                # find train 1 which can arrive 42nd
                                if (item['futureStopData']["127S"][0]['arrivalTime']>line2Arrival42Time):
                                    line1.append(item)
                                    if(line1_min==-1):
                                        line1_i=item
                                        line1_min=item['futureStopData']["127S"][0]['arrivalTime']
                                    elif(line1_min>=item['futureStopData']["127S"][0]['arrivalTime']):
                                        line1_i=item
                                        line1_min=item['futureStopData']["127S"][0]['arrivalTime']

        else:
            for item in items:
                if (item['routeId']=="1"):
                    if( "127S" in item['futureStopData'].keys() and destination in item['futureStopData'].keys()):
                        if('arrivalTime' in item['futureStopData']["127S"][0] and 'arrivalTime' in item['futureStopData'][destination][0]):
                            if(item['futureStopData']["127S"][0]['arrivalTime']!=0 and item['futureStopData'][destination][0]['arrivalTime']!=0):
                                if (item['futureStopData']["127S"][0]['arrivalTime']>line3Arrival42Time):
                                    if(line1_min==-1):
                                        line1_i=item
                                        line1_min=item['futureStopData']["127S"][0]['arrivalTime']
                                    elif(line1_min>=item['futureStopData']["127S"][0]['arrivalTime']):
                                        line1_i=item
                                        line1_min=item['futureStopData']["127S"][0]['arrivalTime']
                                        print "take line3", line1_min

        if(line1_min==-1):
            raise Exception('line 1 data error 1')
        #check if the selected train 1 has arrival time data for 42th anddestination
            if (line1_i['futureStopData']["127S"][0]['arrivalTime']=="0" or line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
                raise Exception('line 1 data error 2')
        else:
            if (line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
                raise Exception('line 1 data error 3')
            line1ArrivalTime = int(line1_i['futureStopData'][destination][0]['arrivalTime'])
            currentTime1 = line1_i['timeStamp']
            line1time = line1ArrivalTime - currentTime1
            print "If you switch, you will arrive at : ", readable_time(line1ArrivalTime), ", take ", line1time, "seconds"
        return True
    else:
        return False


#return bool type, true for switch
def planTripN(source, destination):
    """
    Return: bool type, 'True'-- Switch train
    """
    # Fetch data directly from MTA feed.
    with open('../utils/api_key.txt'', 'rb') as keyfile:
        key = keyfile.read().rstrip('\n')
    tripUpdates = mtaUpdates.mtaUpdates(key)
    items = tripUpdates.getTripUpdates()

    line1,line2,line3=[],[],[]
    line1_min,line2_min,line3_min=-1,-1,-1
    line1Arrival42Time = 0
    for item in items:
        if (item['routeId']=="1"):
            # check if the selected train1 has arrival time data for source
            if( source in item['futureStopData'].keys()):
                if('arrivalTime' in item['futureStopData'][source][0]):
                    if(item['futureStopData'][source][0]['arrivalTime']!=0):
                        line1.append(item)
                        if(line1_min==-1):
                            line1_i=item
                            line1_min=item['futureStopData'][source][0]['arrivalTime']
                        elif(line1_min>=item['futureStopData'][source][0]['arrivalTime']):
                            line1_i=item
                            line1_min=item['futureStopData'][source][0]['arrivalTime']

    if(line1_min==-1):
        raise Exception('line 1 data error 1')
    #check if the selected train 1 has arrival time data for 96th and 42nd
        if (line1_i['futureStopData']["120N"][0]['arrivalTime']=="0" or line1_i['futureStopData']["127N"][0]['arrivalTime']=="0" or line1_i['futureStopData'][source][0]['arrivalTime']=="0" or line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
            raise Exception('line 1 data error 2')
        else:
            line1Arrival42Time=int(line1_i['futureStopData']["127N"][0]['arrivalTime'])

    #find nearest 2,3 train, return if there's an error
    for item in items:
        #case line2
        if(item['routeId']=="2"):
            #check if train 2 has arrival time data for 96th and 42nd
            if("120N" in item['futureStopData'].keys() and "127N" in item['futureStopData'].keys()):
                if(item['futureStopData']["120N"][0]['arrivalTime']=="0" or item['futureStopData']["127N"][0]['arrivalTime']=="0"):
                    raise Exception('line 2 data error')
                elif(int(item['futureStopData']["127N"][0]['arrivalTime'])>line1Arrival42Time):
                    #line2.append(item)
                    if(line2_min==-1):
                        line2_i=item
                        line2_min=int(item['futureStopData']["127N"][0]['arrivalTime'])
                    elif(line2_min>=int(item['futureStopData']["127N"][0]['arrivalTime'])):
                        line2_i=item
                        line2_min=int(item['futureStopData']["127N"][0]['arrivalTime'])
        #case line3
        if(item['routeId']=="3"):
            #check if train 3 has arrival time data for 96th and 42nd
            if("120N" in item['futureStopData'].keys() and "127N" in item['futureStopData'].keys()):
                if(item['futureStopData']["120N"][0]['arrivalTime']=="0" or item['futureStopData']["127N"][0]['arrivalTime']=="0"):
                    raise Exception('line 3 data error')
                elif(int(item['futureStopData']["127N"][0]['arrivalTime'])>line1Arrival42Time):
                    #line3.append(item)
                    if(line3_min==-1):
                        line3_i=item
                        line3_min=int(item['futureStopData']["127N"][0]['arrivalTime'])
                    elif(line3_min>=int(item['futureStopData']["127N"][0]['arrivalTime'])):
                        line3_i=item
                        line3_min=int(item['futureStopData']["127N"][0]['arrivalTime'])

    #Compared the arrival time to 96th of three lines
    line1Arrival96Time=line1_i['futureStopData']["120N"][0]['arrivalTime']
    line2Arrival96Time=line2_i['futureStopData']["120N"][0]['arrivalTime']
    line3Arrival96Time=line3_i['futureStopData']["120N"][0]['arrivalTime']

    # check if the selected train 1 has arrival time for destination
    if (line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
        raise Exception('line 1 data error 3')
    line1ArrivalTime=line1_i['futureStopData'][destination][0]['arrivalTime']
    currentTime1 = line1_i['timeStamp']
    line1time = line1ArrivalTime - currentTime1
    print "If you stay, you will arrive at : ", readable_time(line1ArrivalTime), ", take ", line1time, "seconds"

    if(line1Arrival96Time>line2Arrival96Time or line1Arrival96Time>line3Arrival96Time):
        # If switch, when arrive at 42th, transfer to the nearest line 1
        line1_min=-1
        #If take train2
        if (line2Arrival96Time<line3Arrival96Time):
            for item in items:
                if (item['routeId']=="1"):
                    if( "120N" in item['futureStopData'].keys() and destination in item['futureStopData'].keys()):
                        if('arrivalTime' in item['futureStopData']["120N"][0] ):
                            if(item['futureStopData']["120N"][0]['arrivalTime']!=0 and item['futureStopData'][destination][0]['arrivalTime']!=0):
                                # find train 1 which can arrive 42nd
                                if (item['futureStopData']["120N"][0]['arrivalTime']>line2Arrival96Time):
                                    line1.append(item)
                                    if(line1_min==-1):
                                        line1_i=item
                                        line1_min=item['futureStopData']["120N"][0]['arrivalTime']
                                    elif(line1_min>=item['futureStopData']["120N"][0]['arrivalTime']):
                                        line1_i=item
                                        line1_min=item['futureStopData']["120N"][0]['arrivalTime']

        else:
            for item in items:
                if (item['routeId']=="1"):
                    if( "120N" in item['futureStopData'].keys() and destination in item['futureStopData'].keys()):
                        if('arrivalTime' in item['futureStopData']["120N"][0] and 'arrivalTime' in item['futureStopData'][destination][0]):
                            if(item['futureStopData']["120N"][0]['arrivalTime']!=0 and item['futureStopData'][destination][0]['arrivalTime']!=0):
                                if (item['futureStopData']["120N"][0]['arrivalTime']>line3Arrival96Time):
                                    if(line1_min==-1):
                                        line1_i=item
                                        line1_min=item['futureStopData']["120N"][0]['arrivalTime']
                                    elif(line1_min>=item['futureStopData']["120N"][0]['arrivalTime']):
                                        line1_i=item
                                        line1_min=item['futureStopData']["12ON"][0]['arrivalTime']
                                        print "take line3", line1_min

        if(line1_min==-1):
            raise Exception('line 1 data error 1')
        #check if the selected train 1 has arrival time data for 42th anddestination
            if (line1_i['futureStopData']["120N"][0]['arrivalTime']=="0" or line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
                raise Exception('line 1 data error 2')
        else:
            if (line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
                raise Exception('line 1 data error 3')
            line1ArrivalTime = int(line1_i['futureStopData'][destination][0]['arrivalTime'])
            currentTime1 = line1_i['timeStamp']
            line1time = line1ArrivalTime - currentTime1
            print "If you switch, you will arrive at : ", readable_time(line1ArrivalTime), ", take ", line1time, "seconds"
        return True
    else:
        return False



if __name__ == "__main__":
    main()
