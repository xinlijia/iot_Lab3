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
    tripUpdates = []
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
                update = entity.trip_update
                # Extract trip information.
                # 'currentStopId', 'currentStopStatus', 'vehicleTimeStamp' would be updated by vehicle Message,
                # I set 0 or empty string (default value) to them here. --pg
                t = OrderedDict()
                t['tripId'] = update.trip.trip_id
                t['routeId'] = update.trip.route_id
                t['startDate'] = update.trip.start_date
                t['direction'] = update.trip.direction_id  ####### Need to be converted to 'N'/'S'  --pg
                t['currentStopId'] = ''
                t['currentStopStatus'] = 0
                t['vehicleTimeStamp'] = 0
                # Complicate data structure for 'futureStopData',
                # Refer to assignment's requirement.  --pg
                t['futureStopData'] = OrderedDict()
                for future_stop in update.stop_time_update:
                    stop_id = future_stop.stop_id
                    t['futureStopData'][stop_id] = []
                    t['futureStopData'][stop_id].append(OrderedDict([('arrivalTime',future_stop.arrival.time)]))
                    t['futureStopData'][stop_id].append(OrderedDict([('departureTime',future_stop.departure.time)]))
                t['timeStamp'] = timestamp
                # Add this trip to 'tripUpdates' list.  --pg
                tripUpdates.append(t)

            if entity.vehicle and entity.vehicle.trip.trip_id:
                vehicle = entity.vehicle
                v = OrderedDict()
                v['tripId'] = vehicle.trip.trip_id
                v['routeId'] = vehicle.trip.route_id
                v['startDate'] = vehicle.trip.start_date
                v['direction'] = vehicle.trip.direction_id  ############# Same as above. --pg
                v['currentStopId'] = vehicle.stop_id
                # Set 'currentStopStatus' value. --pg
                if vehicle.current_status == gtfs_realtime_pb2.VehiclePosition.INCOMING_AT:
                    v['currentStopStatus'] = 1
                elif vehicle.current_status == gtfs_realtime_pb2.VehiclePosition.STOPPED_AT:
                    v['currentStopStatus'] = 2
                else:
                    v['currentStopStatus'] = 3
                v['vehicleTimeStamp'] = vehicle.timestamp
                # Add this vehicle update to 'vehicles' list. --pg
                vehicles.append(v)

            if entity.alert:
                # No need to gether info from alert Message.
                pass

        def vehicle_update_trip(t, v):
            '''
            Use info from vehicle Message to update corresponding trips.
            Input:
                t: element in 'tripUpdates' list.
                v: element in 'vehicles' list.
            '''
            t['routeId'] = v['routeId']
            t['startDate'] = v['startDate']
            t['direction'] = v['direction']
            t['currentStopId'] = v['currentStopId']
            t['currentStopStatus'] = v['currentStopStatus']
            t['vehicleTimeStamp'] = v['vehicleTimeStamp']
            return None

        # Update.  --pg
        for v in vehicles:
            for t in tripUpdates:
                if t['tripId'] == v['tripId']:
                    vehicle_update_trip(t, v)

        return self.tripUpdates

        # END OF getTripUpdates method
