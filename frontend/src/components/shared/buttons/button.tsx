import React from "react";

interface ButtonProps {
  type: "button" | "submit";
  variant: "primary" | "secondary";
  text: string;
  onClick?: () => void;
}

export function Button({ type, variant, text, onClick }: ButtonProps) {
  const baseClasses = "px-4 py-2 rounded-lg text-sm font-medium";
  const variantClasses = {
    primary: "bg-primary text-white hover:opacity-80",
    secondary: "bg-[#262626] text-white hover:opacity-80",
  };

  return (
    <button
      type={type}
      onClick={onClick}
      className={`${baseClasses} ${variantClasses[variant]}`}
    >
      {text}
    </button>
  );
}
