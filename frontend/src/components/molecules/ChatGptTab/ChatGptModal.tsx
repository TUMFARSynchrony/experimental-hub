import React, { RefObject, useRef, useState } from "react";
import { Modal, ModalContent, ModalBody, ModalFooter, Button, Progress } from "@nextui-org/react";
import { ChatGptMessage } from "../../../types";
import { ChatGptSpeechBubble } from "../../atoms/ChatMessage/ChatGptSpeechBubble";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPaperPlane } from "@fortawesome/free-solid-svg-icons";
import openAiLogo from "../../molecules/ChatGptTab/ChatGPT_logo.png";

type Props = {
  messageHistory: Array<ChatGptMessage>;
  sendMsgToChatGpt: (message: string, refElement: RefObject<HTMLDivElement>) => void;
  onEnterPressed: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  isTyping: boolean;
  isModalOpen: boolean;
  onOpenChange: () => void;
};

export const ChatGptModal = ({
  messageHistory,
  sendMsgToChatGpt,
  isTyping,
  isModalOpen,
  onOpenChange
}: Props) => {
  const messagesEndRef = useRef(null);
  const [message, setMessage] = useState<string>("");

  const onEnterPressed = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMsgToChatGpt(message, messagesEndRef);
      setMessage("");
    }
  };

  return (
    <>
      <Modal isOpen={isModalOpen} onOpenChange={onOpenChange} placement="center" size="full">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalBody className="overflow-y-auto">
                {" "}
                <div className="flex flex-col h-full w-full items-center">
                  <div className="flex flex-row items-center gap-x-4 border-b-2 border-b-gray-200 w-full py-2 px-6 gap-y-2">
                    <img className="w-12 h-12" src={openAiLogo} />
                    <h3 className="text-3xl">ChatGPT(Beta)</h3>
                  </div>

                  <div className="w-full flex flex-col justify-between overflow-y-auto h-full">
                    <div className="p-4 overflow-y-auto">
                      {messageHistory.map((message, index) => (
                        <div className="py-2" key={index}>
                          <ChatGptSpeechBubble role={message.role} content={message.content} />
                        </div>
                      ))}
                      {isTyping && (
                        <Progress
                          size="sm"
                          isIndeterminate
                          aria-label="Loading..."
                          className="max-w-md py-4"
                        />
                      )}
                      <div ref={messagesEndRef}></div>
                    </div>
                    <div className="flex flex-col p-4 py-8">
                      <div className="relative flex flex-row justify-between gap-x-2 items-center">
                        <textarea
                          className="resize-none border-2 border-stone-300 p-2 py-2 h-full w-full rounded outline-none text-sm"
                          placeholder="Enter your message here"
                          value={message}
                          rows={6}
                          onChange={(event) => setMessage(event.target.value)}
                          onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
                            onEnterPressed(event);
                          }}
                        />
                        <Button
                          className="w-16 rounded-sm absolute right-8 bottom-2"
                          color="primary"
                          size="md"
                          isIconOnly={true}
                          onClick={() => {
                            sendMsgToChatGpt(message, messagesEndRef);
                            setMessage("");
                          }}
                        >
                          <FontAwesomeIcon
                            icon={faPaperPlane}
                            style={{ color: "#ffffff" }}
                            size="lg"
                          />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </ModalBody>
              <ModalFooter></ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  );
};
