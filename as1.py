import mraa
import time
import math
import boto.sns
import json

tempSensor = mraa.Aio(1)
a=tempSensor.read()
R=1023.0/a-1
T=str(1.0/(math.log(R)/4275+1/298.15)-273.15)


conn = boto.sns.connect_to_region("us-east-1",
		aws_access_key_id = '',
		aws_secret_access_key = '')


TOPIC = 'arn:aws:sns:us-east-1:936464516303:Demo_Topic'

pub = conn.publish(topic=TOPIC,message=T)



