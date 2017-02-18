import threading
import time
from datetime import datetime
import boto
import boto.dynamodb2
from pytz import timezone
import calendar

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

# Create New Table. ID as hashkey; Time as RangeKey.
from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey
DYNAMODB_TABLE_NAME = 'add_clean_test'
# ac = Table.create(DYNAMODB_TABLE_NAME, schema=[HashKey('ID'), RangeKey('Time')]);
# Use Existing Table.
ac = Table(DYNAMODB_TABLE_NAME)

### Two functions: adding and cleaning
def adding(table):
    ctr = 0
    while(True):
        try:
            # every 2.5 seconds, add 5 tuples to table
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
        # Keyboard Interrupt to terminate the
        except KeyboardInterrupt:
            print "QUIT adding process."
            break
        finally:
            pass
    return None

def cleaning(table):
    while(True):
        try:
            # every 5 seconds, delete 10s'old tuples
            # Get current time.
            d = datetime.utcnow()
            cur_time = calendar.timegm(d.utctimetuple())
            # Read all data in table.
            all_data = table.scan()
            # Find all old data and delete them.
            for data in all_data:
                if cur_time - int(data['Time']) > 10:
                    data.delete()
            time.sleep(5)
        except keyboardInterrupt:
            print "QUIT cleaning process."
            break
        finally:
            pass

    return None

### Two Threads: adding and cleaning
t1 = threading.Thread(target = adding, name = 'adding', args=(ac,))    # ac: table in DynamoDB
t2 = threading.Thread(target = cleaning, name = 'cleaning', args=(ac,))

# Set to Daemon mode
t1.setDaemon(True)
t2.setDaemon(True)

t1.start()
t2.start()

# Wait for threads t1 & t2 to finish
t1.join()
t2.join()
