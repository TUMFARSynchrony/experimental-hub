import { useAppDispatch, useAppSelector } from "../../../redux/hooks";
import { selectCurrentSession } from "../../../redux/slices/sessionsListSlice";
import { useEffect, useRef, useState } from "react";
import { INITIAL_CHAT_DATA } from "../../../utils/constants";
import { useBackListener } from "../../../hooks/useBackListener";
import useAutosizeTextArea from "../../../hooks/useAutosizeTextArea";
import { useSearchParams } from "react-router-dom";
import { Button } from "@nextui-org/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCircle, faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import { ChatMessage } from "../../../types";
import Select from "react-select";
import { UniformSpeechBubbleParticipant } from "../../atoms/ChatMessage/UniformSpeechBubbleParticipant";
import { getParticipantName } from "../../../utils/utils";

type Props = {
  onChat: (newMessage: ChatMessage) => void;
  onGetSession: (sessionId: string) => void;
  currentUser: string;
  participantId?: string;
  onLeaveExperiment?: () => void;
};

export const ParticipantChatTab = (props: Props) => {
  const { onChat, onGetSession, currentUser, participantId, onLeaveExperiment } = props;
  const [message, setMessage] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();
  const currentSession = useAppSelector(selectCurrentSession);
  const sessionId = currentSession?.id ?? searchParams.get("sessionId");
  const [messageTarget, setMessageTarget] = useState("participants");
  const [shouldShowNotification, setShouldShowNotification] = useState(false);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const dispatch = useAppDispatch();
  useAutosizeTextArea(textAreaRef.current, message);
  useBackListener(() => onLeaveExperiment());

  useEffect(() => {
    if (sessionId) {
      onGetSession(sessionId);
    }
  }, [onGetSession, sessionId]);

  const handleChange = (messageTarget: string) => {
    setMessageTarget(messageTarget);
  };

  const onSendMessage = (messageTarget: string) => {
    if (message.length === 0) {
      return;
    }
    const newMessage = { ...INITIAL_CHAT_DATA };
    newMessage["message"] = message;
    newMessage["time"] = Date.now();
    newMessage["author"] = participantId;
    newMessage["target"] = messageTarget;

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

  const toExperimenter = {
    value: "experimenter",
    label: "To Experimenter"
  };
  const participantOptions =
    currentSession &&
    currentSession.participants
      .filter((p) => p.id !== participantId)
      .map((p, index) => ({
        value: p.id,
        label: p.participant_name
      }));
  participantOptions && participantOptions.unshift(toExperimenter);

  return (
    <div className="flex flex-col border-l-gray-200 border-l-2 h-full w-full items-center">
      <div className="flex flex-col items-center justify-between gap-x-2 border-b-2 border-b-gray-200 w-full py-2 px-6 gap-y-2">
        <div className="text-3xl text-center">Chat</div>
        <div className="flex flex-row justify-center items-center text-sm w-2/3 relative">
          <Select
            className="w-full"
            options={participantOptions}
            defaultValue={toExperimenter}
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
                  <span className="pl-1">{label}</span>
                </>
              ) as unknown as string;
            }}
          />
        </div>
      </div>

      <div className="w-full flex flex-col justify-between overflow-y-auto h-full">
        <div className="p-4 overflow-y-auto">
          {currentUser === "participant" &&
            currentSession &&
            currentSession.participants
              .filter((participant) => participant.id === participantId)
              .map((p) => {
                return p.chat.map((message, index) => (
                  <UniformSpeechBubbleParticipant
                    key={index}
                    message={message.message}
                    author={message.author}
                    target={message.target}
                    date={message.time}
                    sentimentScore={message.sentiment_score}
                    currentParticipantId={participantId}
                    author_name={getParticipantName(message.author, currentSession.participants)}
                    target_name={getParticipantName(message.target, currentSession.participants)}
                  />
                ));
              })}
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
