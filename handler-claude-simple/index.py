import boto3, json, time, random, string, logging, os
from chatResponder import ChatResponder
from botocore.config import Config
# from elevenlabs.client import ElevenLabs
# from elevenlabs import save
from deepgram import DeepgramClient, SpeakOptions
from botocore.exceptions import ClientError

s3_client = boto3.client('s3', config=Config(region_name='us-east-1'))
transcribe_client = boto3.client('transcribe', config=Config(region_name='us-east-1'))
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)


def transcribe_audio(audio_url):
    print("Transcribe audio using AWS Transcribe...")
    print("Audio URL start:", audio_url)
    logging.info(f"Audio URL: {audio_url}")

    # Remove leading/trailing whitespace and single quotes from the audio URL
    audio_url = audio_url.strip().strip("'")

    # Generate a unique job name
    job_name = f"transcribe-job-{int(time.time())}"
    logging.info(f"job_name: {job_name}")

    # Start the transcription job
    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': audio_url},
        MediaFormat='webm',
        LanguageCode='en-US',
        OutputBucketName='awsaudiouploads',
        OutputKey=f'{job_name}-transcript.json',
        Settings={
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': 2
        }
    )

    # Wait for the transcription job to complete
    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            logging.info("job completed or failed")
            break
        time.sleep(5)

    # Retrieve the transcript if the job completed successfully
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        logging.info("Transcription job completed successfully")
        transcript_file_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        logging.info(f"transcript file uri: {transcript_file_uri}")

        transcript_response = s3_client.get_object(Bucket='awsaudiouploads', Key=transcript_file_uri.split("/")[-1])
        transcript = json.loads(transcript_response['Body'].read().decode('utf-8'))
        logging.info(f"transcript: {transcript}")

        transcript_results = transcript['results']['transcripts'][0]['transcript']
        logging.info(f"transcript results: {transcript_results}")

        return transcript_results
    else:
        logging.error("Transcription job not completed successfully")
        raise Exception("Transcription job failed.")


def call_anthropic_bedrock(prompt):

    config = Config(
        region_name='us-east-1'
    )

    client = boto3.client('bedrock-runtime', config=config)

    model_id = 'anthropic.claude-3-haiku-20240307-v1:0'

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }
    request = json.dumps(native_request)

    try:
        # Invoke the model with the request.
        response = client.invoke_model(modelId=model_id, body=request)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)

    # Decode the response body.
    model_response = json.loads(response["body"].read())

    # Extract and print the response text.
    response_text = model_response["content"][0]["text"]
    # print(response_text)

    logging.info(f"Anthropic Bedrock response: {model_response} with text: {response_text}")

    return response_text



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
        chat_string = event['chatString'] # ?? We are getting the chat string from the event and not the userInput??
        logging.info(f"**>> CHAT MESSAGE: {chat_string}")

        # Get the audio URL from the event
        audio_url = event['userInput']['audioFileUrl']
        logging.info(f"**>> URL: {audio_url}")

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
        chatResponder.publish_agent_message(  # TODO: save in database with agent as a "human"
            transcribed_text, audio_url
        )

        # TRANSLATION
        prompt_string = "Human: " + getLanguagePrompt(language_in, language_out, transcribed_text)
        logging.info(f"prompt string: {prompt_string}")

        # Forward the transcribed text to Anthropic Bedrock
        transcribed_text = call_anthropic_bedrock(prompt_string)
        logging.info(f"response from anthropic bedrock: {transcribed_text}")

        # Generate audio from the response from Anthropic Bedrock
        # https://developers.deepgram.com/docs/tts-models for voice selection
        DEEPGRAM_API_KEY = 'Yours goes here'
        DEEPGRAM_API_KEY = '1de775fcceda2010217372f1e57ca0dd3c9226a6'
        model = "aura-angus-en"
        audio_folder = '/tmp'
        if not os.path.exists(audio_folder):
            os.makedirs(audio_folder)

        audio_file_name = f"{makeUniqueKey()}.mp3"
        audio_file_path = os.path.join('/tmp', audio_file_name)
        logging.info(f"audio file name: {audio_file_name}")
        logging.info(f"audio file path: {audio_file_path}")
        # logging.info(f"text to generate voice for: {transcribed_text}")

        try:
            deepgram = DeepgramClient(DEEPGRAM_API_KEY)

            options = SpeakOptions(model=model)

            # generated_audio = deepgram.speak.v("1").save(audio_file_path, transcribed_text, options)
            deepgram.speak.v("1").save(audio_file_path, {"text": transcribed_text}, options)
            # transcribed_text_josn = generated_audio.to_json(indent=4)
            # logging.info(f"transcribed text json: {transcribed_text_josn}")

        except Exception as e:
            logging.info(f"Exception: {e}")

        # Upload the audio to S3
        bucket_name = 'awsaudiouploads'
        audio_key = f'deepgram_audio/{audio_file_name}'
        logging.info(f"audio_key: {audio_key}")

        if os.path.exists(audio_file_path):
            # Upload the file to S3
            try:
                # Upload the file to S3
                s3_client.upload_file(audio_file_path, bucket_name, audio_key)
                logging.info(f"deepgram audio uploaded to: {audio_url}")
            except Exception as e:
                # Handle the upload error
                logging.error(f"Error uploading file to S3: {str(e)}")
                raise e
        else:
            # Handle the file not found error
            logging.error(f"Audio file not found: {audio_file_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        audio_url = f'https://{bucket_name}.s3.amazonaws.com/{audio_key}'

        chatResponder.publish_agent_message(
            transcribed_text, audio_url
        )

    except Exception as e:
        logging.exception("handler: An error occurred")
        print(f"Error from handler: {str(e)}")
        chatResponder.publish_agent_message("Sorry, an error occurred while processing your request.")

    # Mark metadata as done responding
    chatResponder.publish_agent_stop_responding()