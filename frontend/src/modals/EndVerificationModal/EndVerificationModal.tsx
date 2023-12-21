import React from "react";
import { ActionButton } from "../../components/atoms/Button";
import Heading from "../../components/atoms/Heading/Heading";

type Props = {
  setShowModal: React.Dispatch<React.SetStateAction<boolean>>;
  onEndExperiment: () => void;
};

function EndVerificationModal({ setShowModal, onEndExperiment }: Props) {
  const endExperiment = () => {
    setShowModal(false);
    onEndExperiment();
  };

  return (
    <div className="verificationContainer">
      <div className="verificationModal">
        <Heading heading={`Are you sure you want to end the experiment?`} />
        <ActionButton
          text="No"
          variant="contained"
          color="error"
          size="small"
          onClick={() => setShowModal(false)}
        />
        <ActionButton
          text="Yes"
          path="/"
          variant="contained"
          size="small"
          color="success"
          onClick={() => endExperiment()}
        />
      </div>
    </div>
  );
}

export default EndVerificationModal;
