import { Layer, Stage } from "react-konva";
import { Session } from "../../../types";
import { getParticipantById } from "../../../utils/utils";
import type { ConnectedPeer } from "../../../networking/typing";
import Video from "../../atoms/Video/Video";
import { CANVAS_SIZE } from "../../../utils/constants";
import "./VideoCanvas.css";

type Props = {
  connectedParticipants: any;
  sessionData: Session;
  localStream?: any;
  ownParticipantId?: string; // Add a prop for the participant's own ID
};

/** Get the title displayed in a {@link Video} element for `peer`. */
const getVideoTitle = (
  peer: ConnectedPeer,
  index: number,
  ownParticipantId: string,
  sessionData: Session
) => {
  if (peer.summary) {
    if (peer.summary instanceof Object) {
      return `${peer.summary.participant_name}`;
    }
    return ` ${getParticipantById(peer.summary, sessionData).participant_name}`;
  }
  return ownParticipantId ? "You" : `Peer stream ${index + 1}`;
};

function VideoCanvas({ connectedParticipants, sessionData, ownParticipantId, localStream }: Props) {
  return (
    <Stage width={CANVAS_SIZE.width} height={CANVAS_SIZE.height} className="videoCanvas">
      <Layer>
        {/* Render the video for the participant themselves */}
        {ownParticipantId ? (
          <Video
            key="0"
            src={localStream}
            participantData={getParticipantById(ownParticipantId, sessionData)}
            title="You"
            shouldMute={true}
          />
        ) : null}
        {/* Render videos for other connected participants */}
        {connectedParticipants?.map((peer: any, i: number) => {
          const participantData =
            typeof peer.summary === "string"
              ? getParticipantById(peer.summary, sessionData)
              : peer.summary;

          return (
            <Video
              key={i}
              src={peer.stream}
              participantData={participantData}
              title={getVideoTitle(peer, i, ownParticipantId, sessionData)}
            />
          );
        })}
      </Layer>
    </Stage>
  );
}

export default VideoCanvas;
