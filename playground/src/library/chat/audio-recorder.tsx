import React, { useState, useEffect } from "react";
import { Button, Icon, View, Grid, useTheme } from '@aws-amplify/ui-react';
import { ReactMic } from 'react-mic';
import { Auth, Storage } from 'aws-amplify';
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

interface AudioRecorderProps {
  onRecordingComplete: (audioFileUrl: string) => void;
}

export function AudioRecorder({ onRecordingComplete }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlobUrl, setAudioBlobUrl] = useState('');

  //const s3 = new AWS.S3();

const uploadAudioToS3 = async (audioBlob: Blob) => {
  try {
    const currentUser = await Auth.currentAuthenticatedUser();
    const fileName = `audio_${Date.now()}.webm`;
    await Storage.put(fileName, audioBlob, {
      contentType: 'audio/webm',
    });
    const audioFileUrl = await Storage.get(fileName);
    console.log('Audio file uploaded successfully:', audioFileUrl);
    onRecordingComplete(audioFileUrl);
  } catch (error) {
    console.error('Error uploading audio to S3:', error);
  }
};

  const handleRecording = () => {
    if (!isRecording) {
      setIsRecording(true);
      console.log("started recording")
    }
    else {
      setIsRecording(false);
      console.log("stopped recording")
    }
  };
  const startRecording = () => {
    setIsRecording(true);
  };

  const stopRecording = () => {
    setIsRecording(false);
  };

  const onData = (recordedBlob: any) => {
    console.log('chunk of real-time data is: ', recordedBlob);
  };

  const onStop = (recordedBlob: { blobURL: React.SetStateAction<string>; blob: Blob }) => {
    console.log('recordedBlob is: ', recordedBlob);
    setAudioBlobUrl(recordedBlob.blobURL);
    uploadAudioToS3(recordedBlob.blob); // Call the upload function
  };

  const { tokens } = useTheme();

  return (
    <div>
      <Grid
      templateColumns="1fr 1fr 1fr"
      templateRows="4rem"
      gap={tokens.space.small}
      >
        <View>
            <Button id="record-btn"
                    onClick={handleRecording}
                    variation="primary"
                    colorTheme={!isRecording ? 'success' : 'error'}>
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </Button>
        </View>
        <View>
          <ReactMic
            record={isRecording}
            className={'hidden'}
            onStop={onStop}
            onData={onData}
            strokeColor="#000000"
            backgroundColor="rgb(4, 125, 149)" />
        </View>
        <View>
          {audioBlobUrl && <audio src={audioBlobUrl} controls />}
        </View>
      </Grid>
    </div>
  );
}
