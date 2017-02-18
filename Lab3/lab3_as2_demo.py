import threading
import time
from datetime import datetime
import boto
import boto.dynamodb2
from pytz import timezone
import calendar
import logging


### Connect to AWS & Set a new table in Dynamo
# Change 'aws_connect.txt' below to your file.
with open('./aws_connect.txt', 'rb') as aws_file:
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
# ID as hashkey; Time as RangeKey.
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey
DYNAMODB_TABLE_NAME = 'add_clean_test'
# Handle error condition: Creating a table that already exists.
try:
    # Try creating a new table.
    ac = Table.create(DYNAMODB_TABLE_NAME, schema=[HashKey('ID'), RangeKey('Time')])
except boto.exception.JSONResponseError:
    # Use existing table.
    ac = Table(DYNAMODB_TABLE_NAME)


### Two functions: adding and cleaning
# Configure logging: "(threadName) message" format
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-8s) %(message)s',
                    )

def adding(table, run_event):
    logging.debug('Starting.')
    ctr = 0
    # every 2.5 seconds, add 5 tuples to table
    while(run_event.is_set()):
        for i in range(5):
            ctr += 1
            # Get current time in POSIX format & datetime (human-readable) format.
            d = datetime.utcnow()
            cur_time = calendar.timegm(d.utctimetuple())
            cur_time_readable = datetime.fromtimestamp(cur_time, timezone('America/New_York'))
            # Write new data to Dynamo
            table.put_item(
                data={
                    'ID': str(ctr),
                    'Time': str(cur_time),
                    'Time(Readable)':str(cur_time_readable)})
        time.sleep(2.5)

    # run_event is cleared (run_event.is_set() == False), exit the thread
    logging.debug('Exiting.')

    return None

def cleaning(table, run_event):
    logging.debug('Starting.')
    # every 5 seconds, delete all 10-second-old data
    while(run_event.is_set()):
        # Get current time.
        d = datetime.utcnow()
        cur_time = calendar.timegm(d.utctimetuple())
        # Read all data in table.
        all_data = table.scan()
        # Find all old data and delete them.
        for data in all_data:
            if cur_time - int(data['Time']) > 10:
                data.delete()

    # run_event.is_set() == False, exiting the thread.
    logging.debug('Exiting.')

    return None


### MAIN PROGRAM ###
# Set an event for sending the exit signal to threads t1 & t2
run_event = threading.Event()
run_event.set()

# Two Threads: adding and cleaning
t1 = threading.Thread(target = adding, name = 'adding', args=(ac, run_event))    # ac: table in DynamoDB
t2 = threading.Thread(target = cleaning, name = 'cleaning', args=(ac, run_event))

# Set to Daemon mode
t1.setDaemon(True)
t2.setDaemon(True)

t1.start()
t2.start()

try:
    while True:
        time.sleep(0.1)
except keyboardInterrupt:
    print "Keyboard Interrupt, attempting to close the threads."
    # Send exit signals.
    run_event.clear()
    # Wait for t1 & t2 to exit.
    t1.join()
    t2.join()
    print "Threads successfully closed."
