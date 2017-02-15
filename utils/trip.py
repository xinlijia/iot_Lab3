from collections import OrderedDict
# Storing trip related data
# Note : some trips wont have vehicle data
class trip(object):
	def __init__(self):
	    self.tripId = None
	    self.routeId = None
	    self.startDate = None
	    self.direction = None
		self.currentStopId = None
		self.currentStopStatus = None
		self.vehicleTimeStamp = None
		self.futureStopData = OrderedDict() # Format {stopId : [arrivalTime,departureTime]}
		self.timeStamp= None





