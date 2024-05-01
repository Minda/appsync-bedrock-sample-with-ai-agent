import boto3, json, time, logging
from chatResponder import ChatResponder
from botocore.config import Config

bedrock = boto3.client('bedrock-runtime', config=Config(region_name='us-east-1'))
s3_client = boto3.client('s3', config=Config(region_name='us-east-1'))
transcribe_client = boto3.client('transcribe', config=Config(region_name='us-east-1'))
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

def transcribe_audio(audio_url):
    print("transcribe audio... ")
    print("audio url", audio_url)
    logging.info(f"audio url: {audio_url}")

    # Extract the bucket and key from the audio URL
    bucket, key = audio_url.replace("https://s3.amazonaws.com/", "").split("/", 1)

    # Remove leading/trailing whitespace and single quotes from the audio URL
    audio_url = audio_url.strip().strip("'")

    bucket_name = 'awsaudiouploads'
    #file_name = audio_url.split('/')[-1] #get the last element
    #logging.info(f"file_name: {file_name}")

    # deeplearning.io notebook version of file url
    #media_file_uri = f's3://{bucket_name}/{file_name}'
    #logging.info(f"bucket_name: {bucket_name}")

    #logging.info(f"media_file_uri: {media_file_uri}")

    # Generate a unique job name
    job_name = f"transcribe-job-{int(time.time())}"
    logging.info(f"job_name: {job_name}")

    # try:
    # Start the transcription job
    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': audio_url},
        #Media={'MediaFileUri': media_file_uri},
        MediaFormat='webm',
        LanguageCode='en-US',
        OutputBucketName=bucket_name,  # specify the output bucket
        OutputKey=f'{job_name}-transcript.json',
        Settings={
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': 2
        }
    )
    # except Exception as e:
    #     print(f"Error occurred: {e}")
    #     return {
    #         'statusCode': 500,
    #         'body': json.dumps(f"Error occurred: {e}")
    #     }
    #
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps(f"Submitted transcription job for {key} from bucket {bucket}.")
    # }

    # Wait for the transcription job to complete in an infinite loop
    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)

        # break when the status changes
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            logging.info("job completed or failed")
            break
        time.sleep(5)

    # Retrieve the transcript if the job completed successfully
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        logging.info("Transcription job completed successfully")

        # Get the uri from the status
        transcript_file_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        logging.info(f"transcript file uri: {transcript_file_uri}")

        # use the transcript file uri to get an object from s3 bucket
        transcript_response = s3_client.get_object(Bucket='awsaudiouploads', Key=transcript_file_uri.split("/")[-1])

        # load the json object from the response
        transcript = json.loads(transcript_response['Body'].read().decode('utf-8'))
        logging.info(f"transcript: {transcript}")

        transcript_results = transcript['results']['transcripts'][0]['transcript']
        logging.info(f"transcript results: {transcript_results}")

        return transcript_results
    else:
        logging.error("Transcription job not completed successfully")
        raise Exception("Transcription job failed.")

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

def handler(event, context):

    # Setup ability to Respond to chat
    chatResponder = ChatResponder(event['conversationData']['id'])    

    try:
        logging.info("This is an informational message")
        logging.error("This was Minda and Vlad making an catwifhat message")
        logging.info(event)
        #logging.info(event['audioFileUrl'])


        # Get the audio URL from the event
        audio_url = event['chatString']
        # audio_url = event['audioFileUrl']
        language_in = "English"
        language_out = "French"
        tag = "Human: "

        audio_url = audio_url.replace(tag, "")

        #chatResponder.publish_agent_message(audio_url)

        # Transcribe the audio using Amazon Transcribe
        transcribed_text = transcribe_audio(audio_url)
        logging.info(f"transcribed text: {transcribed_text}")

        #TODO: get this into the
        chatResponder.publish_agent_message(f"text from transcription: {transcribed_text}")

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

        prompt_string = "Human: " + lang_prompt
        logging.info(f"prompt string: {prompt_string}")
        # chatResponder.publish_agent_message(f"prompt string: {prompt_string}")

        # Forward the transcribed text to Anthropic Bedrock
        response = anthropic_bedrock(prompt_string)
        chatResponder.publish_agent_message(response)

    except Exception as e:
        logging.exception("handler: An error occurred")
        print(f"Error from handler: {str(e)}")
        chatResponder.publish_agent_message("Sorry, an error occurred while processing your request.")


    # Mark metadata as done responding
    chatResponder.publish_agent_stop_responding()