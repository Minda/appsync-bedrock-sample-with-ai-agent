# AWS AppSync Language Translation Playground

This article is a fork of a sample app provided by AWS. In this version, we've added our own language translation pipeline using AWS transcribe, Claude, and [Deepgram](https://deepgram.com/). 

See this tutorial I wrote for Towards Data Science for detailed instructions on getting your AWS environment set up: 
[The AWS Bedrock Tutorial I Wish I Had: Everything You Need to Know to Prepare Your Machine for AWS Infrastructure](https://towardsdatascience.com/getting-started-how-to-set-up-a-full-stack-app-with-aws-and-bedrock-2b1b158724b8)


## Prerequisites

This project requires the following resources / software available

For the python basted lambda functions

    - Python3
    - Docker
    - Langchain

For deployment of the code to aws

    - Node 16+
    - Yarn
    - Npm
    - AWS CDK
    - An Aws Account

You also need to enable bedrock access to your AWS account.
To do so, navigate to the bedrock console -> manage model access -> enable access for claude

## Setup

Run the following to setup this project.

Note you need docker running to deploy the lambda functions

```
# Start with infra
cd cdk-infrastructure
npm i

# Build TS resolvers into JS
npm run build

# Deploy Infrastructure and populate tables with sample data
npm run deploy
```

Then get the website running

```

# move to playground
cd ../playground

# Load endpoints from deployed stack so we know what api to talk to.
npm run configure

# install dependencies using yarn
yarn

# We are now ready to boot the website
npm run start
```

## Security

See CONTRIBUTING for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
