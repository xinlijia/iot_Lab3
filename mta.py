# *********************************************************************************************
# Usage python mta.py

import json,time,csv,sys
import boto
import boto.dynamodb2
import boto3
from boto3.dynamodb.conditions import Key,Attr

sys.path.append('./utils')
import aws

with open('../aws_connect.txt', 'rb') as aws_file:
    content = aws_file.readlines()
    ACCOUNT_ID = content[0].rstrip('\n').split()[2]
    IDENTITY_POOL_ID = content[1].rstrip('\n').split()[2]
    ROLE_ARN = content[2].rstrip('\n').split()[2]
    aws_file.close()

# Use cognito to setup identity
cognito = boto.connect_cognito_identity()
cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(cognito_id['IdentityId'])
sts = boto.connect_sts()
assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])

# Connect to DynamoDB
# ATTENTION: When using Edison, new table need to be authorized, see Week 3.9
client_dynamo = boto.dynamodb2.connect_to_region(
    'us-east-1',
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)

# Create New Table or use existing table.
# Trip ID as hashkey; Timestamp as RangeKey.
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey

DYNAMODB_TABLE_NAME = "Lab3"
ac = Table(DYNAMODB_TABLE_NAME, connection = client_dynamo)

# prompt
def prompt():
    print ""
    print ">Available Commands are : "
    print "1. plan trip"
    print "2. subscribe to messages"
    print "3. exit"  
    return input()

#return bool type, true for switch
def planTrip():
    line1,line2,line3=[],[],[]
    line1_min,line2_min,line3_min=-1,-1,-1
    items=ac.scan()
    for i in items:
        print i['Future Stop Data']
    #find the nearest 1 train, rerun if there's an error
    for item in items:
        if (item['Route ID']=="1"):
            if('117S' in item['Future Stop Data']):
                if(item['Future Stop Data']["117S"][0]['arrivalTime']=="0"):
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
    

   

        
