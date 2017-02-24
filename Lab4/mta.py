# *********************************************************************************************
# Usage python mta.py

import json,time,csv,sys
import urllib2,contextlib
from datetime import datetime
from pytz import timezone
sys.path.append('/Users/pengguo/Desktop/iot_Lab/utils')  # Path to gtfs_realtime_pb2.py, mtaUpdates.py
import gtfs_realtime_pb2, mtaUpdates
import google.protobuf

# ### Connecting to AWS, DynamoDB ###
# import boto3
# from boto3.dynamodb.conditions import Key,Attr
# import aws
# with open('aws_connect.txt', 'rb') as aws_file:
#     content = aws_file.readlines()
#     ACCOUNT_ID = content[0].rstrip('\n').split()[2]
#     IDENTITY_POOL_ID = content[1].rstrip('\n').split()[2]
#     ROLE_ARN = content[2].rstrip('\n').split()[2]
#     aws_file.close()

# # Use cognito to setup identity
# cognito = boto.connect_cognito_identity()
# cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
# oidc = cognito.get_open_id_token(cognito_id['IdentityId'])
# sts = boto.connect_sts()
# assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])

# # Connect to DynamoDB
# # ATTENTION: When using Edison, new table need to be authorized, see Week 3.9
# client_dynamo = boto.dynamodb2.connect_to_region(
#     'us-east-1',
#     aws_access_key_id=assumedRoleObject.credentials.access_key,
#     aws_secret_access_key=assumedRoleObject.credentials.secret_key,
#     security_token=assumedRoleObject.credentials.session_token)

# # Create New Table or use existing table.
# # Trip ID as hashkey; Timestamp as RangeKey.
# from boto.dynamodb2.table import Table
# from boto.dynamodb2.fields import HashKey, RangeKey

# DYNAMODB_TABLE_NAME = "Lab3"
# ac = Table(DYNAMODB_TABLE_NAME, connection = client_dynamo)

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

def planTrip():
    """
    Return: bool type, 'True'-- Switch train
    """
    # Fetch data directly from MTA feed.
    with open('/Users/pengguo/Desktop/iot_Lab3/utils/api_key.txt', 'rb') as keyfile:
        key = keyfile.read().rstrip('n')
    tripUpdates = mtaUpdates.mtaUpdates(key)
    trip_list = tripUpdates.getTripUpdates()

####################################################################
#     INSTRUCTIONS for data (i.e. trips) in trip_list:
#         trip_list is a list of dictionaries. Every element represents a currently running train (i.e. a trip).
#         For every trip in trip_list:
#             'tripId': Trip's ID, string type.
#             'timeStamp': Time when this feed is sent. POSIX format (i.e., number of seconds since January 1st 1970 00:00:00 UTC). Int type.
#             'routeId': Route's ID, string type. '1','2','3','4','5','5X','6',6X','GS', etc.
#             'startDate': The start date. String type.
#             'direction': Direction that the train is heading to. String type. 'N' or 'S'.
#             'currentStopId': ID of the stop that this train currently stops. String type. Could be empty string.
#             'currentStopStatus': Current stop status of this trip. String type, 'UNKNOWN', 'INCOMING_AT', 'STOPPED_AT' or "IN_TRANSIT_TO".
#             'vehicleTimeStamp': Time when this trip's Vehicle Message is gathered. POSIX format. Int type. Could be 0.
#             'futureStopData': Information about the train's future stops. A dictionary of lists.
#                 Example:
#                     {
#                     '617N' : [{'arrivalTime': 1487747331L}, {'departureTime': 1487747331L}]
#                     '608N' : [{'arrivalTime': 1487748291L}, {'departureTime': 1487748531L}]
#                     '603N' : [{'arrivalTime': 1487748831L}, {'departureTime': 1487748831L}]
#                     '602N' : [{'arrivalTime': 1487748921L}, {'departureTime': 1487748921L}]
#                     '616N' : [{'arrivalTime': 1487747451L}, {'departureTime': 1487747451L}]
#                     '621N' : [{'arrivalTime': 1487746821L}, {'departureTime': 1487746821L}]
#                     '619N' : [{'arrivalTime': 1487747031L}, {'departureTime': 1487747181L}]
#                     '612N' : [{'arrivalTime': 1487747991L}, {'departureTime': 1487747991L}]
#                     '604N' : [{'arrivalTime': 1487748741L}, {'departureTime': 1487748741L}]
#                     '614N' : [{'arrivalTime': 1487747631L}, {'departureTime': 1487747631L}]
#                     '615N' : [{'arrivalTime': 1487747541L}, {'departureTime': 1487747541L}]
#                     '610N' : [{'arrivalTime': 1487748141L}, {'departureTime': 1487748141L}]
#                     '611N' : [{'arrivalTime': 1487748081L}, {'departureTime': 1487748081L}]
#                     '613N' : [{'arrivalTime': 1487747751L}, {'departureTime': 1487747901L}]
#                     '618N' : [{'arrivalTime': 1487747271L}, {'departureTime': 1487747271L}]
#                     '607N' : [{'arrivalTime': 1487748621L}, {'departureTime': 1487748621L}]
#                     '609N' : [{'arrivalTime': 1487748231L}, {'departureTime': 1487748231L}]
#                     '606N' : [{'arrivalTime': 1487748681L}, {'departureTime': 1487748681L}]
#                     '601N' : [{'arrivalTime': 1487749071L}, {'departureTime': 0}]
#                     }
#                 Both 'arrivalTime' and 'departureTime' are int type (actually it's 'long' type).

    # ATTENTION: I HAVE NOT MODIFIED THE CODE BELOW.  
    line1,line2,line3=[],[],[]
    line1_min,line2_min,line3_min=-1,-1,-1
    items=ac.scan()
    # for i in items:
    #     print i['Future Stop Data']
    #find the nearest 1 train, rerun if there's an error
    for item in items:
        if (item['Route ID']=="1"):
            if('117S' in item['Future Stop Data'].keys()):
                print '*************'
                if(item['Future Stop Data']["117S"][0]['arrivalTime']=="0"):
                    print
                    raise Exception('line 1 data error')
                else:
                    if(line1_min==-1):
                        line1_i=item
                        line1_min=int(item['Future Stop Data']["117S"][0]['arrivalTime'])
                    elif(line1_min>=int(item['Future Stop Data']["117S"][0]['arrivalTime'])):
                        line1_i=item
                        line1_min=int(item['Future Stop Data']["117S"][0]['arrivalTime'])
    if(line1_min==-1):
        raise Exception('line 1 data error 1')
    #check if the selected train 1 has arrival time data for 96th and 42th
        if (line1_i['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"]=="0" or line1_i['Future Stop Data']["127"]["L"][0]["M"]['arrivalTime']["N"]=="0"):
            raise Exception('line 1 data error 2')
        else:
            line1Arrival96Time=line1_i['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"]

    #find nearest 2,3 train, rerun if there's an error
    for item in items:
        #case line2
        if(item['Route ID'=="2"]):
            if("120" in item['Future Stop Data'] and "127" in item['Future Stop Data']):
                if(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"]=="0" or item['Future Stop Data']["127"]["L"][0]["M"]['arrivalTime']["N"]=="0"):
                    raise Exception('line 2 data error')
                elif(int(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"])>line1Arrival96Time):
                    #line2.append(item)
                    if(line2_min==-1):
                        line2_i=item
                        line2_min=int(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"])
                    elif(line2_min>=int(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"])):
                        line2_i=item
                        line2_min=int(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"])
        #case line3
        if(item['Route ID'=="3"]):
            if("120" in item['Future Stop Data'] and "127" in item['Future Stop Data']):
                if(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"]=="0" or item['Future Stop Data']["127"]["L"][0]["M"]['arrivalTime']["N"]=="0"):
                    raise Exception('line 3 data error')
                elif(int(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"])>line1Arrival96Time):
                    #line3.append(item)
                    if(line3_min==-1):
                        line3_i=item
                        line3_min=int(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"])
                    elif(line3_min>=int(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"])):
                        line3_i=item
                        line3_min=int(item['Future Stop Data']["120"]["L"][0]["M"]['arrivalTime']["N"])

    #Compared the arrival time on 42th of three lines
    line1Arrival42Time=line1_i['Future Stop Data']["127"]["L"][0]["M"]['arrivalTime']["N"]
    line2Arrival42Time=line2_i['Future Stop Data']["127"]["L"][0]["M"]['arrivalTime']["N"]
    line3Arrival42Time=line3_i['Future Stop Data']["127"]["L"][0]["M"]['arrivalTime']["N"]

    if(line1Arrival42Time>line2Arrival42Time or line1Arrival42Time>line3Arrival42Time):
        return True
    else:
        return False







#send subscribe message to the given phone number
def sendSubMes(phoneNumber):
    pass


def main():
    while(1):
        c=prompt()
        if(c==1):
            try:
                print "Switch" if planTrip()==True else "Stay"
            except Exception as error:
                print "caught an error", error
        elif(c==2):
            phoneNumber=input("enter your phone number: ")
            try:
                sendSubMes(phoneNumber)
            except:
                print "error with phone number"
        elif(c==3):
            return 0
        else:
            print "invalid command!"



if __name__ == "__main__":
    main()
