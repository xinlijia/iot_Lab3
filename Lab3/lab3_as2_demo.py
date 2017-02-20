import threading
import time
from datetime import datetime
import boto
import boto.dynamodb2
from pytz import timezone
import calendar
import logging
import sys
sys.path.append('../utils')
import mtaUpdates

### Connect to AWS & Set a new table in Dynamo
# Change 'aws_connect.txt' below to your file.
with open('/Users/pengguo/Desktop/iot_Lab3/aws_connect.txt', 'rb') as aws_file:
    content = aws_file.readlines()
    ACCOUNT_ID = content[0].rstrip('\n').split()[2]
    IDENTITY_POOL_ID = content[1].rstrip('\n').split()[2]
    ROLE_ARN = content[2].rstrip('\n').split()[2]
    aws_file.close()

# Use cognito to setup identity
cognito = boto.connect_cognito_identity()
cognito_id = cognito.get_id(ACCOUNT_ID, IDENTITY_POOL_ID)
oidc = cognito.get_open_id_token(cognito_id['IdentityId'])
sts = boto.connect_sts()
assumedRoleObject = sts.assume_role_with_web_identity(ROLE_ARN, "XX", oidc['Token'])

# Connect to DynamoDB
# ATTENTION: When using Edison, new table need to be authorized, see Week 3.9
client_dynamo = boto.dynamodb2.connect_to_region(
    'us-east-1',
    aws_access_key_id=assumedRoleObject.credentials.access_key,
    aws_secret_access_key=assumedRoleObject.credentials.secret_key,
    security_token=assumedRoleObject.credentials.session_token)

# Create New Table or use existing table.
# Trip ID as hashkey; Timestamp as RangeKey.
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey
DYNAMODB_TABLE_NAME = 'Lab3'
# Handle error condition: Creating a table that already exists.
try:
    # Try creating a new table.
    ac = Table.create(DYNAMODB_TABLE_NAME, schema=[HashKey('Trip ID'), RangeKey('Timestamp')])
except boto.exception.JSONResponseError:
    # Use existing table.
    ac = Table(DYNAMODB_TABLE_NAME)


### Two functions: adding and cleaning
# Configure logging: "(threadName) message" format
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-8s) %(message)s',
                    )

def adding(table, run_event, tripUpdates):
    logging.debug('Starting.')
    # every 2.5 seconds, add 5 tuples to table
    while(run_event.is_set()):
        # Get data from feed
        update_list = tripUpdates.getTripUpdates()
        for t in update_list:
            # Get current time in datetime (human-readable) format.
            cur_time_readable = datetime.fromtimestamp(t['timeStamp'], timezone('America/New_York'))
            # Write new data to Dynamo
            table.put_item(
                data={
                    'Trip ID': t['tripId'],
                    'Route ID': t['routeId'],
                    'Start Date': t['startDate'],
                    'Direction': t['direction'],
                    'Current Stop ID': t['currentStopId'],
                    'Current Stop Status': t['currentStopStatus'],
                    'Vehicle Timestamp': t['vehicleTimeStamp'],
                    'Future Stop Data': t['futureStopData'],
                    'Timestamp': str(t['timeStamp']),
                    'Timestamp(Readable)': str(cur_time_readable)[0:19]},
                    overwrite = True)

        time.sleep(30)

    # run_event is cleared (run_event.is_set() == False), exit the thread
    logging.debug('Exiting.')

    return None

def cleaning(table, run_event):
    logging.debug('Starting.')
    while(run_event.is_set()):
        # Get current time.
        d = datetime.utcnow()
        cur_time = calendar.timegm(d.utctimetuple())
        # Read all data in table.
        all_data = table.scan()
        # Find all old data and delete them.
        for data in all_data:
            if cur_time - int(data['Timestamp']) >= 120:
                data.delete()
        time.sleep(60)
    # run_event.is_set() == False, exiting the thread.
    logging.debug('Exiting.')

    return None


### MAIN PROGRAM ###
# Set an event for sending the exit signal to threads t1 & t2
run_event = threading.Event()
run_event.set()

# create an mtaUpdates object.
with open('/Users/pengguo/Desktop/iot_Lab3/utils/api_key.txt', 'rb') as keyfile:
    key = keyfile.read().rstrip('n')
tripUpdates = mtaUpdates.mtaUpdates(key)

# Two Threads: adding and cleaning
t1 = threading.Thread(target = adding, name = 'Adding', args=(ac, run_event, tripUpdates))    # ac: table in DynamoDB
t2 = threading.Thread(target = cleaning, name = 'Cleaning', args=(ac, run_event))

# Set to Daemon mode
t1.setDaemon(True)
t2.setDaemon(True)

t1.start()
t2.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print "Keyboard Interrupt, attempting to close the threads."
    # Send exit signals.
    run_event.clear()
    # Wait for t1 & t2 to exit.
    t1.join()
    t2.join()
    print "Threads successfully closed."
