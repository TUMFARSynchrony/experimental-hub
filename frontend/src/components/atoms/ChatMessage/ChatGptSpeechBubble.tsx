type Props = {
  role: string;
  content: string;
};

export const ChatGptSpeechBubble = ({ role, content }: Props) => {
  return (
    <div className="flex flex-col gap-x-1 ">
      <div className="font-bold">
        {role === "system" || role === "assistant" ? "ChatGPT" : "You"}
      </div>
      <div>{content}</div>
    </div>
  );
};
