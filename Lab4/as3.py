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

# 96th street: 120, 120N, 120S
# 42nd street: 127, 127N, 127S

Line1_sta_id = [str(s) for s in range(103, 140)]
Line1_sta_id.append('101')

def staid_to_num(s):
    """
    Parse the Station ID to number.
    '120', '120N', '120S' --> 120
    input: station ID, str type
    return: The number part of station ID, int type
    """
    if s[-1].isalpha():
        return int(s[:-1])
    else:
        return int(s)

def invaild_feed_data():
    print "Invalid feed data. Try it again."
    return -1

def source():
    while 1:
        s = raw_input("Please enter your source station : ")
        if s not in Line1_sta_id:
            print "Invalid source station ID. Try again."
            continue
        else:
            if (120 < int(s) < 127):
                print "please enter a station North of the 96th street or South of 42nd street."
                continue
            else:
                station = int(s)
                break
    return station

def dest():
    while 1:
        s = raw_input("Please enter your source station : ")
        if s not in Line1_sta_id:
            print "Invalid source station ID. Try again."
            continue
        else:
            if (120 < int(s) < 127):
                print "please enter a station North of the 96th street or South of 42nd street."
                continue
            else:
                station = int(s)
                break
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
        mode = input('Please select mode: [1/2/3]')
        if(mode == 3):
            print "Exit."
            return 0
        elif(mode!=1 and mode !=2):
            print "Wrong mode."
        else:
            c=source()
            d=dest()

            if ((c<120 and d<120) or (c>127 and d>127)):
                print "No Line 2 or Line 3 available along your route. No need to switch."
                continue

            if (c == d):
                print "Source and destination are the same. Try again."
                continue
            elif (c<d):
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
            if(mode==2):
                sendSubMes(result)


# send subscribe message to the given phone number
def sendSubMes(result):

    conn = boto.sns.connect_to_region("us-east-1",
                aws_access_key_id = '',
                aws_secret_access_key = '')
    TOPIC = 'arn:aws:sns:us-east-1:936464516303:Demo_Topic'
    add_sub = raw_input("Please input your phone number : ")
    conn.subscribe(TOPIC,"SMS",add_sub)
    pub = conn.publish(topic=TOPIC,message=result)


def planTripS(source, destination):
    """
    Heading south. Decide whether to switch in 96th street(ID: 120/N/S).
    Algorithm:
        1. Identify earliest possible Line 1.
        2. Identify the earliest possible Line 2 or Line 3 after user reaches 96th street.
        3. Compare three trains' arrival time to 42th street(ID: 127/N/S)
    Return:
        1: Switch
        0: Stay
        -1: Invalid feed data.

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
                        line1.append(item)  # all available Line 1 trains
                        if(line1_min==-1):
                            line1_i=item  # line1_i: nearest incoming line 1 train
                            line1_min=item['futureStopData'][source][0]['arrivalTime']  # line1_min:
                        elif(line1_min>=item['futureStopData'][source][0]['arrivalTime']):
                            line1_i=item
                            line1_min=item['futureStopData'][source][0]['arrivalTime']

    if(line1_min==-1):
        #raise Exception('line 1 data error 1')
        return invaild_feed_data()
    else:
        print "Nearest Line 1 train coming at %s." %(readable_time(line1_min))


    #check if the selected train 1 has arrival time data for 96th and 42nd
    if (line1_i['futureStopData']["120S"][0]['arrivalTime']=="0" or line1_i['futureStopData']["127S"][0]['arrivalTime']=="0" or line1_i['futureStopData'][source][0]['arrivalTime']=="0" or line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
        return invaild_feed_data()
        #raise Exception('line 1 data error 2')

    else:
        line1Arrival96Time=int(line1_i['futureStopData']["120S"][0]['arrivalTime'])
        print '\n'
        print "This Line 1 train would arrive at 96th Street at %s." %(readable_time(line1Arrival96Time))

    #find nearest 2,3 train, return if there's an error
    for item in items:
        #case line2
        if(item['routeId']=="2"):
            #check if train 2 has arrival time data for 96th and 42nd
            if("120S" in item['futureStopData'].keys() and "127S" in item['futureStopData'].keys()):
                if(item['futureStopData']["120S"][0]['arrivalTime']=="0" or item['futureStopData']["127S"][0]['arrivalTime']=="0"):
                    return invaild_feed_data()

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
                    #raise Exception('line 3 data error')
                    return invaild_feed_data()
                elif(int(item['futureStopData']["120S"][0]['arrivalTime'])>line1Arrival96Time):
                    #line3.append(item)
                    if(line3_min==-1):
                        line3_i=item
                        line3_min=int(item['futureStopData']["120S"][0]['arrivalTime'])
                    elif(line3_min>=int(item['futureStopData']["120S"][0]['arrivalTime'])):
                        line3_i=item
                        line3_min=int(item['futureStopData']["120S"][0]['arrivalTime'])

    print "If you switch to Line 2, earliest possible Line 2 train would arrive 96th Street at %s." %(readable_time(line2_min))
    print "If you switch to Line 3, earliest possible Line 3 train would arrive 96th Street at %s." %(readable_time(line3_min))

    #Compared the arrival time on 42th of three lines
    line1Arrival42Time=line1_i['futureStopData']["127S"][0]['arrivalTime']
    line2Arrival42Time=line2_i['futureStopData']["127S"][0]['arrivalTime']
    line3Arrival42Time=line3_i['futureStopData']["127S"][0]['arrivalTime']

    # For 3 trains, print arrival time in 42nd St.
    print '\n'
    print "If you stay on Line 1, earliest possible Line 1 would arrive 42nd Street at %s." %(readable_time(line1Arrival42Time))
    print "If you switch to Line 2, earliest possible Line 2 would arrive 42nd Street at %s." %(readable_time(line2Arrival42Time))
    print "If you switch to Line 3, earliest possible Line 3 would arrive 42nd Street at %s." %(readable_time(line3Arrival42Time))

    # check if the selected train 1 has arrival time for destination
    if (line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
        #raise Exception('line 1 data error 3')
        return invaild_feed_data()
    line1ArrivalTime=line1_i['futureStopData'][destination][0]['arrivalTime']
    currentTime1 = line1_i['timeStamp']
    line1time = line1ArrivalTime - currentTime1
    print "If you stay on Line 1, you will arrive at : ", readable_time(line1ArrivalTime), ", take ", line1time, "seconds."

    if(line1Arrival42Time>line2Arrival42Time or line1Arrival42Time>line3Arrival42Time):

        # If switch, when arrive at 42th, transfer to the nearest line 1
        line1_min=-1

        if (line2Arrival42Time<line3Arrival42Time):
            print "Switch to Line 2."
        #If take train2
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
            print "Earliest possible Line 1 train would arrive at %s." %(readable_time(line1_min))

        else:
            print "Switch to Line 3."
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
            print "Earliest possible Line 1 train would arrive at %s." %(readable_time(line1_min))

        if(line1_min==-1):
            #raise Exception('line 1 data error 1')
            return invaild_feed_data()
        #check if the selected train 1 has arrival time data for 42th anddestination
        if (line1_i['futureStopData']["127S"][0]['arrivalTime']=="0" or line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
            #raise Exception('line 1 data error 2')
            return invaild_feed_data()
        else:
            if (line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
                #raise Exception('line 1 data error 3')
                return invaild_feed_data()
            line1ArrivalTime = int(line1_i['futureStopData'][destination][0]['arrivalTime'])
            currentTime1 = line1_i['timeStamp']
            line1time = line1ArrivalTime - currentTime1
            #print "If you switch, you will arrive at : ", readable_time(line1ArrivalTime), ", take ", line1time, "seconds"
            print "This Line 1 train would arrive destination at %s." %(readable_time(line1ArrivalTime))

        return 1
    else:
        print "Stay on Line 1. Would arrive destination at %s." %(readable_time(line1ArrivalTime))
        return 0


#return bool type, true for switch
def planTripN(source, destination):
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

    print "Earliest possible Line 1 train would arrive at %s." %(readable_time(line1_min))
    if(line1_min==-1):
        #raise Exception('line 1 data error 1')
        return invaild_feed_data()
    #check if the selected train 1 has arrival time data for 96th and 42nd
    if (line1_i['futureStopData']["120N"][0]['arrivalTime']=="0" or line1_i['futureStopData']["127N"][0]['arrivalTime']=="0" or line1_i['futureStopData'][source][0]['arrivalTime']=="0" or line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
        #raise Exception('line 1 data error 2')
        return invaild_feed_data()
    else:
        line1Arrival42Time=int(line1_i['futureStopData']["127N"][0]['arrivalTime'])
        print "This Line 1 train would arrive at 42nd Street at %s." %(readable_time(line1Arrival42Time))

    #find nearest 2,3 train, return if there's an error
    for item in items:
        #case line2
        if(item['routeId']=="2"):
            #check if train 2 has arrival time data for 96th and 42nd
            if("120N" in item['futureStopData'].keys() and "127N" in item['futureStopData'].keys()):
                if(item['futureStopData']["120N"][0]['arrivalTime']=="0" or item['futureStopData']["127N"][0]['arrivalTime']=="0"):
                    #raise Exception('line 2 data error')
                    return invaild_feed_data()
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
                    #raise Exception('line 3 data error')
                    return invaild_feed_data()
                elif(int(item['futureStopData']["127N"][0]['arrivalTime'])>line1Arrival42Time):
                    #line3.append(item)
                    if(line3_min==-1):
                        line3_i=item
                        line3_min=int(item['futureStopData']["127N"][0]['arrivalTime'])
                    elif(line3_min>=int(item['futureStopData']["127N"][0]['arrivalTime'])):
                        line3_i=item
                        line3_min=int(item['futureStopData']["127N"][0]['arrivalTime'])

    print "If you switch to Line 2, earliest possible Line 2 train would arrive at %s." %(readable_time(line2_min))
    print "If you switch to Line 3, earliest possible Line 3 train would arrive at %s." %(readable_time(line3_min))

    #Compared the arrival time to 96th of three lines
    line1Arrival96Time=line1_i['futureStopData']["120N"][0]['arrivalTime']
    line2Arrival96Time=line2_i['futureStopData']["120N"][0]['arrivalTime']
    line3Arrival96Time=line3_i['futureStopData']["120N"][0]['arrivalTime']

    print "If you stay on Line 1, earliest possible Line 1 would arrive 96th Street at %s" %(readable_time(line1Arrival96Time))
    print "If you switch to Line 2, earliest possible Line 2 would arrive 96th Street at %s" %(readable_time(line2Arrival96Time))
    print "If you switch to Line 3, earliest possible Line 3 would arrive 96th Street at %s" %(readable_time(line3Arrival96Time))

    # check if the selected train 1 has arrival time for destination
    if (line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
        #raise Exception('line 1 data error 3')
        return invaild_feed_data()
    line1ArrivalTime=line1_i['futureStopData'][destination][0]['arrivalTime']
    currentTime1 = line1_i['timeStamp']
    line1time = line1ArrivalTime - currentTime1
    print "If you stay, you will arrive at : ", readable_time(line1ArrivalTime), ", take ", line1time, "seconds"

    if(line1Arrival96Time>line2Arrival96Time or line1Arrival96Time>line3Arrival96Time):
        # If switch, when arrive at 42th, transfer to the nearest line 1
        line1_min=-1
        #If take train2
        if (line2Arrival96Time<line3Arrival96Time):
            print "Switch to Line 2."
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
            print "Earliest possible Line 1 train would arrive at 96th Street at %s." %(readable_time(line1_min))

        else:
            print "Switch to Line 3."
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
            print "Earliest possible Line 1 train would arrive at 96th Street at %s." %(readable_time(line1_min))

        if(line1_min==-1):
            #raise Exception('line 1 data error 1')
            return invaild_feed_data()
        #check if the selected train 1 has arrival time data for 42th anddestination
        if (line1_i['futureStopData']["120N"][0]['arrivalTime']=="0" or line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
            #raise Exception('line 1 data error 2')
            return invaild_feed_data()
        else:
            if (line1_i['futureStopData'][destination][0]['arrivalTime']=="0"):
                #raise Exception('line 1 data error 3')
                return invaild_feed_data()
            line1ArrivalTime = int(line1_i['futureStopData'][destination][0]['arrivalTime'])
            currentTime1 = line1_i['timeStamp']
            line1time = line1ArrivalTime - currentTime1
            print "If you switch, you will arrive at : ", readable_time(line1ArrivalTime), ", take ", line1time, "seconds"
        print "You would arrive at destination at %s." %(readable_time(line1ArrivalTime))
        return 1
    else:
        print "Stay on Line 1."
        print "You would arrive at destination at %s." %(readable_time(line1ArrivalTime))
        return 0



if __name__ == "__main__":
    main()
