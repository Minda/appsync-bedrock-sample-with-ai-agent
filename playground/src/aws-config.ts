import AWS from 'aws-sdk';

if (!process.env.REACT_APP_REGION || !process.env.REACT_APP_IDENTITY_POOL_ID) {
  throw new Error('Required AWS configuration is missing. Please check your .env file');
}


AWS.config.update({
  region: process.env.REACT_APP_REGION,
  credentials: new AWS.CognitoIdentityCredentials({
    IdentityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID,
  }),
});

export default AWS;