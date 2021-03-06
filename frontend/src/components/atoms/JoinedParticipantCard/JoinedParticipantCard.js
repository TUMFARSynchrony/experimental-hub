import { useState } from "react";
import JoinedParticipantModal from "../../../modals/JoinedParticipantModal/JoinedParticipantModal";
import Button from "../Button/Button";
import Label from "../Label/Label";
import "./JoinedParticipantCard.css";

function JoinedParticipant({ participantData, sessionId }) {
  const [showModal, setShowModal] = useState(false);

  const onClick = () => {
    setShowModal(!showModal);
  };

  return (
    <div className="joinedParticipantContainer">
      <Label
        title={participantData.first_name + " " + participantData.last_name}
      />
      <Button
        name={"More info"}
        design={"secondary"}
        onClick={() => onClick()}
      />
      {showModal && (
        <JoinedParticipantModal
          participantData={participantData}
          showModal={showModal}
          setShowModal={setShowModal}
          sessionId={sessionId}
        />
      )}
    </div>
  );
}

export default JoinedParticipant;
