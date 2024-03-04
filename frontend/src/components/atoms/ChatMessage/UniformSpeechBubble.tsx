import moment from "moment";
import { SentimentScore } from "../../../types";
import { calculateColor } from "./utils";

type Props = {
  author: string;
  target: string;
  message: string;
  date: number;
  currentUser: string;
  participant_name: string;
  sentimentScore?: SentimentScore;
};
export const UniformSpeechBubble = (props: Props) => {
  const { author, target, message, date, currentUser, participant_name, sentimentScore } = props;

  const setMessageTexts = (author: string) => {
    if (author === "experimenter" && target === "participants") {
      return `Me to Participants (Announcement)`;
    } else if (author === "experimenter" && target !== "participants") {
      return `Me to ${participant_name} (Privately)`;
    } else {
      return `${participant_name} to Me (Privately)`;
    }
  };
  return (
    <div className="flex flex-col">
      <div className="flex flex-row justify-between">
        <div className="self-start text-[0.75rem] pt-1.5">{setMessageTexts(author)}</div>
        <div className="self-end text-[0.65rem] max-w-full">{moment(date).format("lll")}</div>
      </div>
      <div className="flex flex-row justify-between items-center gap-x-4">
        <div className="self-start bg-blue-600 text-white px-2 py-1 rounded break-words max-w-full text-start">
          {message}
        </div>
        {sentimentScore && (
          <div
            className="px-2 py-1 rounded text-white text-xs font-bold"
            style={{ backgroundColor: calculateColor(sentimentScore.score, sentimentScore.label) }}
          >
            {sentimentScore.score.toFixed(3)}
          </div>
        )}
      </div>
    </div>
  );
};
