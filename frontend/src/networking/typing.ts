/**
 * Message send by / to the backend.
 * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#message Message data type documentation.
 */
export type Message = {
  type: string;
  data: any;
};

/**
 * Check if `data` is a valid {@link Message}.
 * Does not check the type or contents of the `data` field in message.
 * Only checks if the required fields exist, not for unwanted fields or invalid contents.
 *
 * @param data data that should be checked for {@link Message} type
 * @returns true if `data` is a valid {@link Message}
 */
export function isValidMessage(data: any): data is Message {
  return "type" in data && typeof data.type === "string" && "data" in data;
}

/**
 * Check if `data` is a valid {@link RTCSessionDescriptionInit}.
 * Only checks if the required fields exist, not for unwanted fields or invalid contents.
 *
 * @param data data that should be checked for {@link RTCSessionDescriptionInit} type
 * @returns true if `data` is a valid {@link RTCSessionDescriptionInit}
 */
function isValidConnectionRTCSessionDescriptionInit(data: any): data is RTCSessionDescriptionInit {
  return "sdp" in data && "type" in data;
}

/**
 * Connection proposal.
 * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#connectionproposal ConnectionProposal data type documentation.
 */
export type ConnectionProposal = {
  id: string;
  participant_summary: ParticipantSummary | string | null;
};

/**
 * Check if `data` is a valid {@link ConnectionProposal}.
 * Only checks if the required fields exist, not for unwanted fields or invalid contents.
 *
 * @param data data that should be checked for {@link ConnectionProposal} type
 * @returns true if `data` is a valid {@link ConnectionProposal}
 */
export function isValidConnectionProposal(data: any): data is ConnectionProposal {
  return "id" in data && "participant_summary" in data;
}

/**
 * Connection offer.
 * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#connectionoffer ConnectionOffer data type documentation.
 */
export type ConnectionOffer = {
  id: string;
  offer: RTCSessionDescriptionInit;
};

/**
 * Connection answer.
 * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#connectionanswer ConnectionAnswer data type documentation.
 */
export type ConnectionAnswer = {
  id: string;
  answer: RTCSessionDescriptionInit;
};

/**
 * New ICE candidate.
 */
export type IceCandidate = {
  id: string;
  candidate: RTCIceCandidate;
};

/**
 * Check if `data` is a valid {@link ConnectionAnswer}.
 * Only checks if the required fields exist, not for unwanted fields or invalid contents.
 *
 * @param data data that should be checked for {@link ConnectionAnswer} type
 * @returns true if `data` is a valid {@link ConnectionAnswer}
 */
export function isValidConnectionAnswer(data: any): data is ConnectionAnswer {
  return (
    "id" in data && "answer" in data && isValidConnectionRTCSessionDescriptionInit(data.answer)
  );
}

/**
 * Summary of a participant.
 * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#participantsummary ParticipantSummary data type documentation.
 */
export type ParticipantSummary = {
  participant_name: string;
  position: {
    x: number;
    y: number;
    z: number;
  };
  size: {
    width: number;
    height: number;
  };
  chat: {
    message: string;
    time: number;
    author: string;
    target: string;
  }[];
};

/**
 * Information about a connected peer the {@link Connection} has.
 */
export type ConnectedPeer = {
  stream: MediaStream;
  summary: ParticipantSummary | string | null;
};
