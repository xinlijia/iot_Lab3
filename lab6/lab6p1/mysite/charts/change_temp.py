#!/usr/bin/env python
#-*- coding:utf-8 -*-


import random
import time
from charts.models import chart
from django.utils import timezone
import mraa
import math

def add():
    obj = chart.objects.all()
    obj.delete()
    count = 0
    tempSensor = mraa.Aio(1)

    while count<10:
        count += 1
        a=tempSensor.read()
        t = round(1.0/(math.log(1023.0/a-1)/4275+1/298.15)-273.15, 2)
        chart.objects.create(temp=t, timestamp=timezone.now())
        time.sleep(1)
    return True


