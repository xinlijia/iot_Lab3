#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import random
import time
from charts.models import chart
from django.utils import timezone
import math


def add():
    obj = chart.objects.all()
    obj.delete()
    with open('t.txt', 'rb') as f:
    	for line in f:
	 	t = float(line)
		tem = round(t,2)
		ttime = time.time() 
        	chart.objects.create(temp=tem, timestamp=timezone.now(), floattime=ttime)
    return True



