#To do:
#1. repeatition dealing
#2. add direction updates



import urllib2,contextlib
from datetime import datetime
from collections import OrderedDict

from pytz import timezone
import gtfs_realtime_pb2
import google.protobuf

import vehicle,alert,tripupdate,trip

class mtaUpdates(object):

    # Do not change Timezone
    TIMEZONE = timezone('America/New_York')
    
    # feed url depends on the routes to which you want updates
    # here we are using feed 1 , which has lines 1,2,3,4,5,6,S
    # While initializing we can read the API Key and add it to the url
    feedurl = 'http://datamine.mta.info/mta_esi.php?feed_id=1&key='
    
    VCS = {1:"INCOMING_AT", 2:"STOPPED_AT", 3:"IN_TRANSIT_TO"}    
    #tripUpdates = []
    #alerts = []
    trips=[]
    vehicles=[]

    def __init__(self,apikey):
        self.feedurl = self.feedurl + apikey

    # Method to get trip updates from mta real time feed
    def getTripUpdates(self):
        feed = gtfs_realtime_pb2.FeedMessage()
        try:
            with contextlib.closing(urllib2.urlopen(self.feedurl)) as response:
                d = feed.ParseFromString(response.read())
        except (urllib2.URLError, google.protobuf.message.DecodeError) as e:
            print "Error while connecting to mta server " +str(e)
	

	timestamp = feed.header.timestamp
        nytime = datetime.fromtimestamp(timestamp,self.TIMEZONE)
	
	for entity in feed.entity:
            if entity.trip_update and entity.trip_update.trip.trip_id:
		new = trip.trip()
                exist=0
                for old in trips:
                    if old.tripId == entity.trip_update.trip.trip_id:
                        new = old
                        exist=1
                        break
                #for updates in entity:
                #naive approach, not consider repeatition
                if(entity.trip_update.trip.start_date):
                    new.startDate=entity.trip_update.trip.start_date
                if(entity.trip_update.trip.route_id):
                    new.routeId=entity.trip_update.trip.route_id
                if(entity.trip_update.stop_time_update.stop_id):
                    if(entity.trip_update.stop_time_update.arrival):
                    #update arrival
                        new.futureStopData[stop_id][0]=entity.trip_update.stop_time_update.arrival.time
                    if(entity.trip_update.stop_time_update.departure):
                    #update departure
                        new.futureStopData[stop_id][1]=entity.trip_update.stop_time_update.departure.time

                trip.timeStamp=entity.id
                if(exist==0):
                    trip.append(new)

	    if entity.vehicle and entity.vehicle.trip.trip_id:
	    	new = trip.trip()
                exist=0
                for old in trips:
                    if(old.tripId==entity.vehicle.trip.trip_id):
                        new = old
                        exist=1
                        break
                if(entity.vehicle.trip.start_date):
                    new.startDate=entity.vehicle.trip.start_date
                if(entity.vehicle.trip.route_id):
                    new.routeId=entity.vehicle.trip.route_id
                if(entity.vehicle.current_status):
                    new.currentStopStatus=entity.vehicle.current_status
                if(entity.vehicle.stop_id):
                    new.currentStopId=entity.vehicle.stop_id
                if(entity.vehicle.time_stamp):
                    new.vehicleTimeStamp=entity.vehicle.time_stamp

                trip.timeStamp=entity.id
                if(exist==0):
                    trip.append(new)

	    if entity.alert:
                new = trip.trip()
            # no need to update

	return self.tripUpdates
    
    # END OF getTripUpdates method
