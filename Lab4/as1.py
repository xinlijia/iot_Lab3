import mraa
import time
import math
import boto.sns
import json

tempSensor = mraa.Aio(1)
a=tempSensor.read()
R=1023.0/a-1
T=str(1.0/(math.log(R)/4275+1/298.15)-273.15)

# Read key files
with open('/Users/pengguo/Desktop/sns_key.txt', 'rb') as aws_file:
	lines = aws_file.readlines()
	access_key_id = lines[0].rstrip('\n')
	secret_access_key = lines[1].rstrip('\n')

# Connect to Amazon AWS
conn = boto.sns.connect_to_region("us-east-1",
		aws_access_key_id = access_key_id,
		aws_secret_access_key = secret_access_key)


TOPIC = 'arn:aws:sns:us-east-1:936464516303:Demo_Topic'

pub = conn.publish(topic=TOPIC,message=T)
