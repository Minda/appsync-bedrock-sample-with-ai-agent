import React, { useEffect, useState, useCallback, useRef } from "react";
import { useParams } from "react-router-dom";
import { useAgentApiAgent, useAgentApiSendMessage, useAgentApiSubscribeConversation } from "../apis/agent-api";
import { Loader, TextAreaField, View, Flex, Card } from "@aws-amplify/ui-react";
import { Container } from "../library/container";
import { ChatRendered } from "../library/chat/chat-rendered";
import { useAgentApiConversation } from "../apis/agent-api/hooks/useConversations";
import { useAgentConversationMetadata, useResetAgentConversationMetadata } from "../apis/agent-api/hooks/useMetadata";
import { AudioRecorder } from "../library/chat/audio-recorder";
import { LanguageSelector } from "../library/chat/language-selector";

export function AIAgentViewChat() {
    const { chatId } = useParams();
    const conversationObject = useAgentApiConversation(chatId);
    const agentObject = useAgentApiAgent(conversationObject.value?.agent);
    const [chatString, setChatString] = useState<string>("");
    const conversationMetadata = useAgentConversationMetadata();
    const resetMetadata = useResetAgentConversationMetadata();
    const submitMessage = useAgentApiSendMessage(chatId);
    useAgentApiSubscribeConversation(chatId);

    const [languageIn, setLanguageIn] = useState("English");
    const [languageOut, setLanguageOut] = useState("French");

    // Use refs to store the latest language values
    const languageInRef = useRef(languageIn);
    const languageOutRef = useRef(languageOut);

    const handleLanguageChange = useCallback((newLanguageIn: string, newLanguageOut: string) => {
        console.log('handleLanguageChange called with:', newLanguageIn, newLanguageOut);
        setLanguageIn(newLanguageIn);
        setLanguageOut(newLanguageOut);
        // Update refs
        languageInRef.current = newLanguageIn;
        languageOutRef.current = newLanguageOut;
    }, []);

    const handleRecordingComplete = useCallback(async (audioUrl: string) => {
        console.log('Handling the completed recording..');
        console.log('Audio URL:', audioUrl);
        console.log('Language In:', languageInRef.current);
        console.log('Language Out:', languageOutRef.current);

        submitMessage({
            message: audioUrl,
            audioFileUrl: audioUrl,
            languageIn: languageInRef.current,
            languageOut: languageOutRef.current
        });
    }, [submitMessage]);

    useEffect(() => {
        console.log('AIAgentViewChat - languageIn:', languageIn, 'languageOut:', languageOut);
        // Update refs when state changes
        languageInRef.current = languageIn;
        languageOutRef.current = languageOut;
    }, [languageIn, languageOut]);

    useEffect(() => {
        if (conversationMetadata.partialMessage && !conversationMetadata.responding) {
            resetMetadata();
        }
    }, [chatId, resetMetadata, conversationMetadata]);

    if (conversationObject.isUnloaded() || !conversationObject.value || agentObject.isUnloaded() || !agentObject.value) {
        return <Loader />;
    }


    return (
        <Flex>
            <View width={900}>
                <Container heading={`Translation`} minHeight={500} padBody={0}>
                    <ChatRendered/>
                </Container>
                <Card justify-content="center">
                    <Flex direction={'row'} alignContent={'center'} justify-content="center" >

                        <View >
                            <AudioRecorder onRecordingComplete={handleRecordingComplete}/>
                        </View>


                    </Flex>
                </Card>

                <Card>
                    {
                        conversationMetadata.responding && <Loader variation="linear"/>
                    }
                    {
                        !conversationMetadata.responding && <TextAreaField
                            labelHidden
                            className={'hidden'}
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
                <Container heading="Language">
                  <LanguageSelector
                    languageIn={languageIn}
                    languageOut={languageOut}
                    onLanguageChange={handleLanguageChange}
                  />
                </Container>
            </View>
        </Flex>
    )
}