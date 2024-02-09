import { instructionsList } from "../../../utils/constants";
import { FormControlLabel, Checkbox } from "@mui/material";
import React, { useState, useEffect } from "react";

interface InstructionsTabProps {
  onInstructionsCheckChange: (consent: boolean) => void;
}

const InstructionsTab = ({ onInstructionsCheckChange }: InstructionsTabProps) => {
  const [checkedInstructions, setCheckedInstructions] = useState(
    instructionsList.map(() => false) // Initialize all checkboxes as unchecked
  );

  useEffect(() => {
    // Calculate whether all checkboxes are checked
    const allChecked = checkedInstructions.every((checked) => checked);
    onInstructionsCheckChange(allChecked); // Pass the status to the parent component
  }, [checkedInstructions, onInstructionsCheckChange]);

  const handleCheckboxChange = (index: number) => {
    const newCheckedInstructions = [...checkedInstructions];
    newCheckedInstructions[index] = !newCheckedInstructions[index];
    setCheckedInstructions(newCheckedInstructions);
  };

  return (
    <div className="flex flex-col p-4 border-l-gray-100 border-l-2 h-[calc(100vh-4rem)] w-full items-center gap-y-5">
      <div className="text-3xl">Instructions</div>
      <div className="w-full flex flex-col h-full items-start space-y-6">
        {instructionsList.map((instruction, index) => (
          <FormControlLabel
            key={index}
            control={
              <Checkbox
                checked={checkedInstructions[index]}
                onChange={() => handleCheckboxChange(index)}
              />
            }
            label={instruction}
          />
        ))}
      </div>
    </div>
  );
};

export default InstructionsTab;
