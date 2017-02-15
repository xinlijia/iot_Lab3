# *********************************************************************************************
# Program to update dynamodb with latest data from mta feed. It also cleans up stale entried from db
# Usage python dynamodata.py
# *********************************************************************************************
import json,time,sys
from collections import OrderedDict
from threading import Thread

import boto3
from boto3.dynamodb.conditions import Key,Attr

sys.path.append('../utils')
import tripupdate,vehicle,alert,mtaUpdates,aws

### YOUR CODE HERE ####

#adding data task
def adding():
	try:
		while(1):
			time.sleep(30)
			newData=mtaUpdate.getTripUpdates()
			mtadata.put_item(data=newData)
	except KeyboardInterrupt:
		exit

#cleaning data task
def cleaning():
	try:
		while(1):
			time.sleep(60)
			resultSet=mtadata.scan()
			i=0
			l=len(resultSet)
			for trips in resultSet:
				if l-i>4:
					trips.delete()
				i+=1

	except KeyboardInterrupt:
		exit

client_dynamo = getClient()

#users = Table.create('mtadata', schema=[HashKey('tripId')], connection=client_dynamo)
mtadata = Table('mtadata',connection=client_dynamo)


with open('./key.txt', 'rb') as keyfile:
        APIKEY = keyfile.read().rstrip('\n')
        keyfile.close()
mtaUpdate=mtaUpdate(APIKEY)


t1 = threading.Thread(name='adding',target=adding)
t2 = threading.Thread(name='cleaning',target=cleaning)
t1.start()
t2.start()

