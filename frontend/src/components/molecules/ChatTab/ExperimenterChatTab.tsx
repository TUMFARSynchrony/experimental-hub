import { useAppDispatch, useAppSelector } from "../../../redux/hooks";
import { updateLastMessageReadTime } from "../../../redux/slices/sessionsListSlice";
import { useEffect, useRef, useState } from "react";
import { INITIAL_CHAT_DATA } from "../../../utils/constants";
import { SpeechBubble } from "../../atoms/ChatMessage/SpeechBubble";
import { useBackListener } from "../../../hooks/useBackListener";
import useAutosizeTextArea from "../../../hooks/useAutosizeTextArea";
import { useSearchParams } from "react-router-dom";
import { Button } from "@nextui-org/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import { ChatMessage, Participant, Session } from "../../../types";
import Select from "react-select";
import { faCircle } from "@fortawesome/free-solid-svg-icons";
import { UniformSpeechBubble } from "../../atoms/ChatMessage/UniformSpeechBubble";

type Props = {
  onChat: (newMessage: ChatMessage) => void;
  onGetSession: (sessionId: string) => void;
  currentUser: string;
  participantId?: string;
  onLeaveExperiment?: () => void;
  onSendSessionToBackend?: (session: Session) => void;
  onUpdateMessageReadTime?: (participantId: string, lastReadTime: number) => void;
};

export const ExperimenterChatTab = (props: Props) => {
  const {
    onChat,
    onGetSession,
    currentUser,
    participantId,
    onLeaveExperiment,
    onUpdateMessageReadTime
  } = props;
  const [message, setMessage] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();
  const currentSession = useAppSelector((state) => state.sessionsList.currentSession);
  const participants = useAppSelector((state) => state.sessionsList.currentSession.participants);
  const sessionId = currentSession?.id ?? searchParams.get("sessionId");
  const [messageTarget, setMessageTarget] = useState("participants");
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const dispatch = useAppDispatch();
  useAutosizeTextArea(textAreaRef.current, message);
  useBackListener(() => onLeaveExperiment());

  useEffect(() => {
    if (sessionId) {
      onGetSession(sessionId);
    }
  }, [onGetSession, sessionId, messageTarget]);

  const handleChange = (messageTarget: string) => {
    const now = Date.now();
    setMessageTarget(messageTarget);
    dispatch(updateLastMessageReadTime({ id: messageTarget, time: now }));
    if (messageTarget !== "participants") {
      onUpdateMessageReadTime(messageTarget, now);
    }
  };
  const onSendMessage = (messageTarget: string) => {
    if (message.length === 0) {
      return;
    }
    const newMessage = { ...INITIAL_CHAT_DATA };
    newMessage["message"] = message;
    newMessage["time"] = Date.now();
    newMessage["author"] = participantId ? participantId : "experimenter";
    newMessage["target"] = participantId ? "experimenter" : messageTarget;
    onChat(newMessage);
    onGetSession(sessionId);

    setMessage("");
  };
  const onEnterPressed = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      onSendMessage(messageTarget);
    }
  };

  const hasUnreadMessages = (participants: Array<Participant>) => {
    return currentSession.participants.some((p) => p.lastMessageSentTime > p.lastMessageReadTime);
  };

  const toAllParticipantOption = {
    value: "participants",
    label: "To all participants",
    shouldShowNotification: false
  };
  const participantOptions =
    currentSession &&
    participants.map((p, index) => ({
      value: p.id,
      label: p.participant_name,
      shouldShowNotification: p.lastMessageSentTime > p.lastMessageReadTime
    }));
  participantOptions.unshift(toAllParticipantOption);
  return (
    <div className="flex flex-col border-l-gray-200 border-l-2 h-full w-full items-center">
      <div className="flex flex-col items-center justify-between gap-x-2 border-b-2 border-b-gray-200 w-full py-2 px-6 gap-y-2">
        <h3 className="text-3xl">Chat</h3>

        <div className="flex flex-row justify-center items-center text-sm w-2/3 relative">
          <div className="absolute z-10 translate-x-1/2 left-0">
            {currentSession && hasUnreadMessages(currentSession.participants) && (
              <FontAwesomeIcon icon={faCircle} style={{ color: "#fb6641" }} />
            )}
          </div>
          <Select
            className="w-full"
            options={participantOptions}
            defaultValue={toAllParticipantOption}
            onChange={(event) => handleChange(event.value)}
            isSearchable={false}
            getOptionLabel={(props: any) => {
              const { value, label, shouldShowNotification } = props;
              return (
                <>
                  <div className="absolute translate-x-1/2 left-0">
                    {shouldShowNotification && (
                      <FontAwesomeIcon icon={faCircle} style={{ color: "#fb6641" }} />
                    )}
                  </div>
                  <span className="pl-4">{label}</span>
                </>
              ) as unknown as string;
            }}
          />
        </div>
      </div>

      <div className="w-full flex flex-col justify-between overflow-y-auto h-full">
        <div className="p-4 overflow-y-auto">
          {currentUser === "experimenter" &&
            currentSession &&
            messageTarget !== "participants" &&
            participants
              .find((participant) => participant.id === messageTarget)
              .chat.filter((m, i) => m.author === "experimenter" || m.target === "experimenter")
              .map((message, index) => (
                <SpeechBubble
                  key={index}
                  currentUser={currentUser}
                  message={message.message}
                  author={message.author}
                  target={message.target}
                  date={message.time}
                  sentimentScore={message.sentiment_score}
                />
              ))}
          {currentSession &&
            messageTarget === "participants" &&
            currentUser === "experimenter" &&
            (() => {
              // Flatten the chat messages into a single array
              const allMessages = currentSession.participants.flatMap((p) =>
                p.chat.map((message) => ({
                  message: message.message,
                  author: message.author,
                  target: message.target,
                  time: new Date(message.time).getTime(), // Convert time to a sortable format
                  participant_name: p.participant_name,
                  sentiment_score: message.sentiment_score && message.sentiment_score
                }))
              );

              // Create a set to track unique messages based on time, author, and message
              const uniqueMessagesSet = new Set();

              // Filter the messages to exclude duplicates
              const filteredMessages = allMessages.filter((message) => {
                if (message.author !== "experimenter" && message.target !== "experimenter") {
                  return false;
                }
                const messageKey = `${message.time}-${message.author}-${message.message}`;
                if (!uniqueMessagesSet.has(messageKey)) {
                  uniqueMessagesSet.add(messageKey);
                  return true;
                }
                return false;
              });

              // Sort the filtered messages by their time property
              filteredMessages.sort((a, b) => a.time - b.time);

              // Render the sorted filtered messages
              return filteredMessages.map((message, index) => (
                <UniformSpeechBubble
                  key={index}
                  currentUser={currentUser}
                  message={message.message}
                  author={message.author}
                  target={message.target}
                  date={message.time}
                  participant_name={message.participant_name}
                  sentimentScore={message.sentiment_score}
                />
              ));
            })()}
        </div>
        <div className="flex flex-col p-4 py-8">
          <div className="flex flex-row justify-between gap-x-2 items-center">
            <textarea
              className="resize-none border-2 border-stone-300 p-2 py-2 h-full w-full rounded outline-none text-sm"
              placeholder="Enter your message here"
              value={message}
              ref={textAreaRef}
              rows={1}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
                onEnterPressed(event);
              }}
            />
            <Button
              className="h-8 rounded-sm"
              color="primary"
              size="md"
              isIconOnly={true}
              onClick={() => onSendMessage(messageTarget)}
            >
              <FontAwesomeIcon icon={faPaperPlane} style={{ color: "#ffffff" }} />{" "}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
