import moment from "moment";
import { SentimentScore } from "../../../types";
import { calculateColor } from "./utils";

type Props = {
  author: string;
  target: string;
  message: string;
  date: number;
  sentimentScore: SentimentScore;
  currentParticipantId: string;
  author_name: string;
  target_name: string;
};
export const UniformSpeechBubbleParticipant = (props: Props) => {
  const {
    author,
    target,
    message,
    date,
    sentimentScore,
    currentParticipantId,
    author_name,
    target_name
  } = props;
  console.log(author, target);
  const setMessageTexts = (author: string) => {
    if (author === currentParticipantId && target !== "experimenter") {
      return `Me to ${target_name} (Privately)`;
    } else if (author === currentParticipantId && target === "experimenter") {
      return `Me to Experimenter (Privately)`;
    } else if (author === "experimenter" && target === currentParticipantId) {
      return `Experimenter to Me (Privately)`;
    } else if (author === "experimenter" && target === "participants") {
      return `Experimenter to Me (Announcement)`;
    } else {
      return `${author_name} to Me (Privately)`;
    }
  };
  return (
    <div className="flex flex-col">
      <div className="flex flex-row justify-between">
        <div className="self-start text-[0.75rem] pt-1.5">{setMessageTexts(author)}</div>
        <div className="self-end text-[0.65rem] max-w-full">{moment(date).format("lll")}</div>
      </div>
      <div className="flex flex-row justify-between">
        <div className="self-start bg-blue-600 text-white px-2 py-1 rounded break-words max-w-full text-start">
          {message}
        </div>
        <div>
          {sentimentScore && (
            <div
              className="px-2 py-1 rounded text-white font-bold text-xs"
              style={{
                backgroundColor: calculateColor(sentimentScore.score, sentimentScore.label)
              }}
            >
              {sentimentScore.score.toFixed(3)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
