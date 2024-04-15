import AWS from 'aws-sdk';

AWS.config.update({
  region: 'us-east-1',
  credentials: new AWS.CognitoIdentityCredentials({
    IdentityPoolId: 'us-east-1:ec2240ed-1b9c-41f4-a234-47be0ac1ea70',
  }),
});

export default AWS;