import React from "react";
import Button, { ButtonProps } from "@mui/material/Button";
import { useNavigate } from "react-router-dom";

interface ActionIconButtonProps extends ButtonProps {
  text: string;
  icon: JSX.Element;
  path?: string;
  onClick?: () => void;
}

function ActionIconButton({
  text,
  variant,
  color,
  size,
  onClick,
  icon,
  path
}: ActionIconButtonProps) {
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
      startIcon={icon}
    >
      {text}
    </Button>
  );
}

export default ActionIconButton;
