console.log('Loading function');

exports.handler = (event, context, callback) => {
    //console.log('Received event:', JSON.stringify(event, null, 2));
    var AWS = require('aws-sdk');
    var ml = new AWS.MachineLearning();
    var endpointUrl = 'https://realtime.machinelearning.us-east-1.amazonaws.com';
    var mlModelId = 'ml-iUzgFok8Zie';
    var numMessagesProcessed = 0;
    var numMessagesToBeProcessed = event.Records.length;
    event.Records.forEach((record) => {
        // Kinesis data is base64 encoded so decode here
        const payload = new Buffer(record.kinesis.data, 'base64').toString('ascii');
        console.log('Decoded payload:', payload);
    });
    callback(null, `Successfully processed ${event.Records.length} records.`);
    
    var callPredict = function(tweetData){{
    console.log('calling predict');
    ml.predict(
      {
        Record : tweetData,
        PredictEndpoint : endpointUrl,
        MLModelId: mlModelId
     },
      function(err, data) {{
        if (err) {{
          console.log(err);
          context.done(null, 'Call to predict service failed.');
        }}
        else {{
          console.log('Predict call succeeded');
          if(data.Prediction.predictedLabel === '1'){{
            console.log('result: 1');
          }}
          else{{
            console.log('result:0');
          }}
        }}
      }}
      );
  }};
  
  var processRecords = function(){{
    for(i = 0; i < numMessagesToBeProcessed; ++i) {{
      encodedPayload = event.Records[i].kinesis.data;
      // Amazon Kinesis data is base64 encoded so decode here
      payload = new Buffer(encodedPayload, 'base64').toString('utf-8');
      console.log("payload:"+payload);
      try {{
        parsedPayload = JSON.parse(payload);
        callPredict(parsedPayload);
      }}
      catch (err) {{
        console.log(err, err.stack);
        context.done(null, "failed payload"+payload);
      }}
    }}
  }};

  var checkRealtimeEndpoint = function(err, data){{
    if (err){{
      console.log(err);
      context.done(null, 'Failed to fetch endpoint status and url.');
    }}
    else {{
      var endpointInfo = data.EndpointInfo;

      if (endpointInfo.EndpointStatus === 'READY') {{
        endpointUrl = endpointInfo.EndpointUrl;
        console.log('Fetched endpoint url :'+endpointUrl);
        processRecords();
      }} else {{
        console.log('Endpoint status : ' + endpointInfo.EndpointStatus);
        context.done(null, 'End point is not Ready.');
      }}
    }}
  }};
