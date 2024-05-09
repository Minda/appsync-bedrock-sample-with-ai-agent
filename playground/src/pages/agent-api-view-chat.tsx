import { useParams } from "react-router-dom"
import { useAgentApiAgent, useAgentApiSendMessage, useAgentApiSubscribeConversation } from "../apis/agent-api"
import { Loader, TextAreaField, View, Flex, Card, SelectField } from "@aws-amplify/ui-react" //ui.docs.amplify.aws/react
import { Container } from "../library/container"
import { ChatRendered } from "../library/chat/chat-rendered"
import { useEffect, useState } from "react"
import { AIAgentChatConnections } from "./agent-api-chat-connections"
import { useAgentApiConversation } from "../apis/agent-api/hooks/useConversations"
import { useAgentConversationMetadata, useResetAgentConversationMetadata } from "../apis/agent-api/hooks/useMetadata"
import {AudioRecorder} from "../library/chat/audio-recorder";
import { LanguageSelector } from "../library/chat/LanguageSelector";

/*
* Chat Dialog & Actions
* */

export function AIAgentViewChat () {
    
    const {chatId} = useParams()
    const conversationObject = useAgentApiConversation(chatId)
    const agentObject = useAgentApiAgent(conversationObject.value?.agent)
    const [chatString, setChatString] = useState<string>()
    const conversationMetadata = useAgentConversationMetadata()
    const resetMetadata = useResetAgentConversationMetadata()
    const submitMessage = useAgentApiSendMessage(chatId)
    useAgentApiSubscribeConversation(chatId)

    const [langIn, setLanguageIn] = useState("English");
    const [langOut, setLanguageOut] = useState("French");

    //TODO: Add a lanuage selector
    //https://ui.docs.amplify.aws/react/components/selectfield

    //@ts-nocheck
    useEffect(() => {
        if (conversationMetadata.partialMessage && !conversationMetadata.responding) {
            resetMetadata()
        }
    }, [chatId, resetMetadata, conversationMetadata])

    if (conversationObject.isUnloaded() || !conversationObject.value || agentObject.isUnloaded() || !agentObject.value) {
        return <Loader/>
    }

 const handleLanguageChange = (newLanguageIn: string, newLanguageOut: string) => {
    console.log('Language In:', newLanguageIn);
    console.log('Language Out:', newLanguageOut);
    setLanguageIn(newLanguageIn);
    setLanguageOut(newLanguageOut);
  };

  const handleRecordingComplete = async (audioUrl: string) => {
      console.log('Handling the completed recording..');
      console.log('Audio URL: ', audioUrl);
      console.log('Language In: ', langIn);
      console.log('Language Out: ', langOut);

      const chatString = ""+audioUrl;

      submitMessage({
          message: chatString,
          audioFileUrl: audioUrl,
          languageIn: langIn,
          languageOut: langOut
      });
    };

    /* ... other components */
    return (
        <Flex>
            <View width={900}>
                <Container heading={`Chatting with '${agentObject.value.name}'`} minHeight={500} padBody={0}>
                    <ChatRendered/>
                </Container>
                <Card>
                    <Flex direction={'row'} alignContent={'center'} >

                        <View >
                            <AudioRecorder onRecordingComplete={handleRecordingComplete}/>
                        </View>
                        <LanguageSelector onLanguageChange={handleLanguageChange} />

                    </Flex>
                </Card>

                <Card>
                    {
                        conversationMetadata.responding && <Loader variation="linear"/>
                    }
                    {
                        !conversationMetadata.responding && <TextAreaField
                            labelHidden
                            label="Message"
                            placeholder="Type your message here"
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    const audioFileUrl = "http://www.testurl.com"
                                    setChatString('')
                                    e.preventDefault()
                                }
                            }}
                            value={chatString}
                            onChange={(e) => {
                                setChatString(e.target.value)
                            }} 
                        />
                    }
                </Card>
            </View>
            <View width={300}>
                <AIAgentChatConnections/>
            </View>
        </Flex>
    )
}