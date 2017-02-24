# *********************************************************************************************
# Usage python mta.py

import json,time,csv,sys
import boto
import boto.dynamodb2
import boto.sns
import boto3
from boto3.dynamodb.conditions import Key,Attr
import urllib2,contextlib
from datetime import datetime
from pytz import timezone
sys.path.append('../utils')  
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

# prompt
def prompt():
    print ""
    print ">Available Commands are : "
    print "1. plan trip"
    print "2. subscribe to messages"
    print "3. exit"  
    return input()

def readable_time(time):
    """
    Convert POSIX time format to human-readable format.
    "YYYY-MM-DD HH:MM:SS"
    """
    return str(datetime.fromtimestamp(time, timezone('America/New_York')))[0:19]

def main():
    result = ''
    while(1):
        c=prompt()
        if(c==1):
            if (planTrip()== True):
                result = 'Switch'
            else:
                result = 'Stay'
            print result
        elif(c==2):
            try:
                print result
                sendSubMes(result)
            except:
                print "error with phone number"
        elif(c==3):
            return 0
        else:
            print "invalid command!"

#return bool type, true for switch
def planTrip():
    """
    Return: bool type, 'True'-- Switch train
    """
    # Fetch data directly from MTA feed.
    with open('api_key.txt', 'rb') as keyfile:
        key = keyfile.read().rstrip('n')
    tripUpdates = mtaUpdates.mtaUpdates(key)
    items = tripUpdates.getTripUpdates()

    line1,line2,line3=[],[],[]
    line1_min,line2_min,line3_min=-1,-1,-1
    line1Arrival96Time = 0
    for item in items:
        if (item['routeId']=="1"):
            if("117S" in item['futureStopData'].keys()):
                if('arrivalTime' in item['futureStopData']["117S"][0]):
                    if(item['futureStopData']["117S"][0]['arrivalTime']!=0):
                        line1.append(item)
                        if(line1_min==-1):
                            line1_i=item
                            line1_min=item['futureStopData']['117S'][0]['arrivalTime']
                        elif(line1_min>=item['futureStopData']['117S'][0]['arrivalTime']):
                            line1_i=item
                            line1_min=item['futureStopData']['117S'][0]['arrivalTime']

    if(line1_min==-1):
        raise Exception('line 1 data error 1')
    #check if the selected train 1 has arrival time data for 96th and 42th
        if (line1_i['futureStopData']["120S"][0]['arrivalTime']=="0" or line1_i['futureStopData']["127S"][0]['arrivalTime']=="0"):
            raise Exception('line 1 data error 2')
        else:
            line1Arrival96Time=int(line1_i['futureStopData']["120S"][0]['arrivalTime'])

    #find nearest 2,3 train, rerun if there's an error
    for item in items:
        #case line2
        if(item['routeId']=="2"):
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
    currentTime = time.time()
    line1time = line1Arrival42Time - currentTime
    line2time = line2Arrival42Time - currentTime
    line3time = line3Arrival42Time - currentTime
    print "If you take line 1, you will arrive 42 nd street at : ", readable_time(line1Arrival42Time), ", take ", line1time, "seconds"
    print "If you take line 2, you will arrive 42 nd street at : ", readable_time(line2Arrival42Time), ", take ", line2time, "seconds"
    print "If you take line 3, you will arrive 42 nd street at : ", readable_time(line3Arrival42Time), ", take ", line3time, "seconds"
    if(line1Arrival42Time>line2Arrival42Time or line1Arrival42Time>line3Arrival42Time):
        return True
    else:
        return False


# send subscribe message to the given phone number
def sendSubMes(result):

    conn = boto.sns.connect_to_region("us-east-1",
                aws_access_key_id = '',
                aws_secret_access_key = '')

     
    TOPIC = 'arn:aws:sns:us-east-1:936464516303:Demo_Topic'

    add_sub = raw_input("Please input your phone number : ")

    conn.subscribe(TOPIC,"SMS",add_sub)

    pub = conn.publish(topic=TOPIC,message=result)



if __name__ == "__main__":
    main()
    