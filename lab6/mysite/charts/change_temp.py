
import sys
import random
import time
from charts.models import chart
from django.utils import timezone
import math
import mraa
from time import strftime, gmtime

def add():
    tempSensor = mraa.Aio(1)
    a=tempSensor.read()
    t = round(1.0/(math.log(1023.0/a-1)/4275+1/298.15)-273.15, 2)
    ttime = time.time()
    ts = str(strftime("%H:%M:%S", gmtime())) 
    chart.objects.create(temp=t, timestamp=ts, floattime=ttime)
    return True



