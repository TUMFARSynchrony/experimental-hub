import React from "react";
import Button, { ButtonProps } from "@mui/material/Button";
import { useNavigate } from "react-router-dom";

interface ActionButtonProps extends ButtonProps {
  text: string;
  path?: string;
  onClick?: () => void;
}

function ActionButton({
  text,
  variant,
  color,
  size,
  onClick,
  disabled = false,
  path
}: ActionButtonProps) {
  const navigate = useNavigate();

  const handleButtonClick = () => {
    if (path) {
      navigate(path);
    }
    if (onClick) {
      onClick();
    }
  };

  return (
    <Button
      variant={variant}
      color={color}
      size={size}
      onClick={handleButtonClick}
      disabled={disabled}
    >
      {text}
    </Button>
  );
}

export default ActionButton;
