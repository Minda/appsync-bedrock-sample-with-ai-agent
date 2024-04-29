import boto3, json, time, logging
from chatResponder import ChatResponder
from botocore.config import Config

bedrock = boto3.client('bedrock-runtime', config=Config(region_name='us-east-1'))
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

def transcribe_audio(audio_url):

    print("transcribe audio... ")
    print(audio_url)

    # Extract the bucket and key from the audio URL
    bucket, key = audio_url.replace("https://s3.amazonaws.com/", "").split("/", 1)

    # Generate a unique job name
    job_name = f"transcribe-job-{int(time.time())}"

    # Start the transcription job
    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': audio_url},
        MediaFormat='webm',
        LanguageCode='en-US'
    )

    # Wait for the transcription job to complete
    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(5)

    # Retrieve the transcript if the job completed successfully
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        transcript_file_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcript_response = s3_client.get_object(Bucket='aws-audio-recordings', Key=transcript_file_uri.split("/")[-1])
        transcript = json.loads(transcript_response['Body'].read().decode('utf-8'))
        return transcript['results']['transcripts'][0]['transcript']
    else:
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

        chatResponder.publish_agent_message("activated handler")
        # Get the audio URL from the event
        audio_url = event['chatString']
        # audio_url = event['audioFileUrl']
        audio_url = audio_url.replace("Human: ", "")

        chatResponder.publish_agent_message(audio_url)

        # Transcribe the audio using Amazon Transcribe
        transcribed_text = transcribe_audio(audio_url)

        chatResponder.publish_agent_message(transcribed_text)

        # Forward the transcribed text to Anthropic Bedrock
        response = anthropic_bedrock(transcribed_text)
        chatResponder.publish_agent_message(response)

    except Exception as e:
        logging.exception("handler: An error occurred")
        print(f"Error from handler: {str(e)}")
        chatResponder.publish_agent_message("Sorry, an error occurred while processing your request.")


    # Mark metadata as done responding
    chatResponder.publish_agent_stop_responding()