import boto3, json, time, random, string, logging, os
from chatResponder import ChatResponder
from botocore.config import Config
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from botocore.exceptions import ClientError

bedrock = boto3.client('bedrock-runtime', config=Config(region_name='us-east-1'))
s3_client = boto3.client('s3', config=Config(region_name='us-east-1'))
#transcribe_client = boto3.client('transcribe', config=Config(region_name='us-east-1'))
runtime_client = boto3.client('sagemaker-runtime', config=Config(region_name='us-east-1'))
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

def transcribe_audio(audio_url):
    print("Transcribe audio using Whisper model on SageMaker...")
    print("Audio URL start:", audio_url)
    logging.info(f"Audio URL: {audio_url}")

    # Extract the bucket and key from the audio URL
    #bucket, key = audio_url.replace("https://s3.amazonaws.com/", "").split("/", 1)
    bucket = 'awsaudiouploads'

    key = audio_url.split('amazonaws.com/')[1]

    #key = 'audio_uploads/test-audio.webm'
    #file_name = 'test-audio.webm'

    file_name = os.path.basename(audio_url)

    # Remove leading/trailing whitespace and single quotes from the audio URL
    audio_url = audio_url.strip().strip("'")
    logging.info(f"Bucket: {bucket}")
    logging.info(f"Key: {key}")
    logging.info(f"File name: {file_name}")

    #role = "arn:aws:iam::908166648332:role/service-role/AmazonSageMaker-ExecutionRole-20240515T103026"

    #s3_path = 's3://mindabucket/whisper/code/whisper-model.tar.gz'

    # Sagemaker runtime client
    runtime_client = boto3.client('sagemaker-runtime')

    # Download audio file from s3
    #s3 = boto3.client('s3')

    #Check if the object exists in bucket
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        logging.info(f"Response (head object): {response}")
    except ClientError as e:
        if e.response['Error']['Code'] == '403':
            print("Error: Access denied. Check your IAM permissions and bucket policy.")
        else:
            print("Error:", e)

    #Create a local path to download the audio file
    local_audio_path = os.path.join('/tmp', file_name)
    logging.info(f"Local audio path: {local_audio_path}")

    #Download the audio file from S3
    try:
        s3_client.download_file(bucket, key, local_audio_path)
    except Exception as e:
        logging.info(f"Error downloading file from S3: {str(e)}")
        raise

    # Read the audio file
    with open(local_audio_path, "rb") as f:
        data = f.read()

    logging.info(f'Data: {data}')

    # Invoke endpoint with Sagemaker runtime client
    response = runtime_client.invoke_endpoint(
        EndpointName='huggingface-pytorch-inference-2024-05-22-17-41-26-525',  # Replace with your endpoint name
        ContentType='audio/x-audio',
        Body=data
    )

    # Process the response and extract the transcription result
    result = json.loads(response['Body'].read().decode())
    transcribed_text = result['text']

    logging.info(f"Transcribed text: {transcribed_text}")
    return transcribed_text

def anthropic_bedrock (prompt):

    response = bedrock.invoke_model(
        body=json.dumps({
            "prompt": prompt + "\nAssistant: ",
            "max_tokens_to_sample":500,
            "temperature":0,
            "top_k":250,
            "top_p":0.999,
            "stop_sequences":[],
            "anthropic_version":"bedrock-2023-05-31",
        }),
        modelId='anthropic.claude-v2'
    )

    raw_body = response['body'].read().decode("utf-8")
    response_json = json.loads(raw_body)
    
    return (([*response_json.values()][0]))

def makeUniqueKey():
    timestamp = int(time.time())
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return f"{timestamp}_{random_string}"
    # timestamp = int(time.time())
    # random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def getLanguagePrompt(language_in, language_out, transcribed_text):
    lang_prompt = f'''You will be acting as a professional interpreter.
            User will provide you with a text in {language_in}.
            You will respond with a translated text from {language_in} to {language_out}.
            You will NOT include a translation of this message into your response.
            You will happily translate text with technical terms and long text.
            You will absolutely NOT respond with anything other than the translated text.
            ---
            Here is the text you need to translate:
            {transcribed_text}
            '''
    return lang_prompt

def handler(event, context):

    # Setup ability to Respond to chat
    chatResponder = ChatResponder(event['conversationData']['id'])    

    try:
        logging.info(event)

        # Get the chat message from the event
        chat_string = event['chatString']
        logging.info(f"**>> CHAT MESSAGE: {chat_string}")

        # Get the audio URL from the event
        audio_url = event['userInput']['audioFileUrl']
        logging.info(f"**>> URL: {audio_url}")
        #chatResponder.publish_agent_message(f"URL: {audio_url}")

        # Get the language in and language out TODO: from the event
        # language_in = "English"
        # language_out = "French"
        language_in = event['userInput']['languageIn']
        language_out = event['userInput']['languageOut']
        logging.info(f"**>> LANGUAGE IN: {language_in}")
        logging.info(f"**>> LANGUAGE OUT: {language_out}")
        tag = "Human: "

        # TRANSCRIPTION
        # Transcribe the audio using Amazon Transcribe
        transcribed_text = transcribe_audio(audio_url.replace(tag, ""))
        logging.info(f"transcribed text: {transcribed_text}")
        chatResponder.publish_agent_message( #TODO: save in database with agent as a "human"
            transcribed_text, audio_url
        )

        #TRANSLATION
        prompt_string = "Human: " + getLanguagePrompt(language_in, language_out, transcribed_text)
        logging.info(f"prompt string: {prompt_string}")

        # Forward the transcribed text to Anthropic Bedrock
        response = anthropic_bedrock(prompt_string)
        logging.info(f"response from anthropic bedrock: {response}")

        # Generate audio from the response from Anthropic Bedrock
        client = ElevenLabs(api_key="26b568cd9804dc5c637bf7176bda54b7")
        audio = client.generate(
            text=response,
            voice="Arnold",
            model='eleven_multilingual_v2'
        )

        audio_file_name = f"{makeUniqueKey()}.mp3"
        audio_file_path = os.path.join('/tmp', audio_file_name)
        logging.info(f"audio file name: {audio_file_name}")
        logging.info(f"audio file path: {audio_file_path}")

        #Save the audio to a file
        save(audio, audio_file_path)

        #Upload the audio to S3
        bucket_name = 'awsaudiouploads'
        audio_key = f'audio/{audio_file_name}'
        logging.info(f"audio_key: {audio_key}")

        s3_client.upload_file(audio_file_path, bucket_name, audio_key)
        audio_url = f'https://{bucket_name}.s3.amazonaws.com/{audio_key}'
        logging.info(f"audio_url: {audio_url}")

        chatResponder.publish_agent_message(
            response, audio_url
        )

    except Exception as e:
        logging.exception("handler: An error occurred")
        print(f"Error from handler: {str(e)}")
        chatResponder.publish_agent_message("Sorry, an error occurred while processing your request.")


    # Mark metadata as done responding
    chatResponder.publish_agent_stop_responding()