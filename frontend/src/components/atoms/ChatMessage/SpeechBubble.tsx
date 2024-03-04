import moment from "moment";
import { SentimentScore } from "../../../types";
import { calculateColor } from "./utils";

type Props = {
  author: string;
  target: string;
  message: string;
  date: number;
  currentUser: string;
  color?: string;
  sentimentScore?: SentimentScore;
};
export const SpeechBubble = (props: Props) => {
  const { author, target, message, date, currentUser, color, sentimentScore } = props;
  const shouldApplySelfEnd = (): boolean => {
    if (author === "experimenter" && currentUser === "experimenter") {
      return true;
    } else if (author === "experimenter" && currentUser !== "experimenter") {
      return false;
    } else return !(author !== "experimenter" && currentUser === "experimenter");
  };
  return (
    <div className="flex flex-col">
      <div
        className={`${shouldApplySelfEnd() ? "self-end" : "self-start"} text-[0.65rem] max-w-full`}
      >
        {moment(date).format("lll")}
      </div>
      <div
        className={`flex ${
          shouldApplySelfEnd() ? "flex-row-reverse" : "flex-row"
        } justify-between items-center gap-x-4`}
      >
        <div
          className={`${
            shouldApplySelfEnd()
              ? "self-end bg-stone-200"
              : `self-start ${color ? color : "bg-blue-600"} text-white`
          } px-2 py-1 rounded break-words max-w-full text-start`}
        >
          {message}
        </div>
        {sentimentScore && (
          <div
            className="px-2 py-1 rounded text-white font-bold text-xs"
            style={{ backgroundColor: calculateColor(sentimentScore.score, sentimentScore.label) }}
          >
            {sentimentScore.score.toFixed(3)}
          </div>
        )}
      </div>
    </div>
  );
};
