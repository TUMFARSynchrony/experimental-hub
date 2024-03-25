import React, { useEffect, useRef } from "react";
import { Image, Group, Text } from "react-konva";
import { useUserStream } from "./Streams";
import { CanvasElement, Participant } from "../../../types";
import Konva from "konva";
import { useAppSelector } from "../../../redux/hooks";
import { useSearchParams } from "react-router-dom";
import { selectCurrentSession } from "../../../redux/slices/sessionsListSlice";

type VideoProps = {
  src: MediaProvider;
  participantData: Participant;
  title?: string; // Add a title prop
  shouldMute?: boolean;
};

const Video = ({ src, participantData, title, shouldMute }: VideoProps) => {
  const session = useAppSelector(selectCurrentSession);
  const [searchParams, setSearchParams] = useSearchParams();
  const activeParticipantId = searchParams.get("participantId");
  const activeParticipant = session.participants.find(
    (participant) => participant.id === activeParticipantId
  ) || { view: [] as CanvasElement[] };
  const asymmetricViewCheck = activeParticipant.view.length > 0;
  const videoData = asymmetricViewCheck
    ? activeParticipant.view.find(
        (participant) => participant.id === participantData.canvas_id
      ) || { size: { width: 0, height: 0 }, position: { x: 0, y: 0, z: 0 } }
    : participantData;

  const useVideo = (stream: MediaStream | null) => {
    const videoRef = useRef(document.createElement("video"));

    useEffect(() => {
      const video = videoRef.current;
      if (!stream) {
        return;
      }

      if (shouldMute) {
        video.muted = true;
      }

      video.srcObject = src;
      video.onloadedmetadata = function () {
        video.play();
      };
    }, [stream]);

    return videoRef.current;
  };

  const stream = useUserStream();
  const video = useVideo(stream);
  const shapeRef: React.MutableRefObject<Konva.Image> = useRef();

  useEffect(() => {
    const interval = setInterval(() => {
      shapeRef?.current.getLayer()?.batchDraw();
    }, 1000 / 50);

    return () => {
      clearInterval(interval);
    };
  }, [video]);

  return (
    <Group>
      <Image
        ref={shapeRef}
        image={video}
        width={videoData.size.width}
        height={videoData.size.height}
        x={videoData.position.x}
        y={videoData.position.y}
      />
      <Text
        text={title}
        fontSize={16}
        fontFamily="Arial"
        fill="black"
        align="center"
        x={videoData.position.x} // Adjust X-coordinate to position the title
        y={videoData.position.y + videoData.size.height} // Adjust Y-coordinate to position below the video
        width={videoData.size.width}
      />
    </Group>
  );
};

export default Video;
