import mraa
import math
import time
import sys

def main():
    tempSensor = mraa.Aio(1)
    temp = []
    count = 0
    with open('../t.txt', 'wb') as f:
        f.close()
    time.sleep(1)
    while count<10:
        count += 1
        a=tempSensor.read()
        t = str(round(1.0/(math.log(1023.0/a-1)/4275+1/298.15)-273.15, 2))
	print t
        with open('../t.txt', 'ab') as f:
            f.write(t+'\n')
            f.close()
	time.sleep(1)        

if __name__ == "__main__":
    main()
