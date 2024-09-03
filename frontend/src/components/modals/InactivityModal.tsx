import React from "react";
import clsx from "clsx";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "./confirmation-modals/BaseModal";
import ModalBody from "./ModalBody";
import ModalButton from "../buttons/ModalButton";
import { formatMs } from "#/utils/formatMs";

interface TimeoutBadgeProps {
  from: number; // in milliseconds
  className?: React.HTMLProps<HTMLDivElement>["className"];
}

function TimeoutBadge({ from, className }: TimeoutBadgeProps) {
  const [time, setTime] = React.useState(from);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setTime((prev) => prev - 1000);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className={clsx(
        "bg-[#FFCFD3] py-[10px] px-[15px] rounded-[20px] flex items-center justify-center",
        "text-[#EF3744] text-sm font-[500]",
        className,
      )}
    >
      {formatMs(time)}
    </div>
  );
}

function InactivityModal() {
  return (
    <ModalBody>
      <div className="flex flex-col gap-2">
        <TimeoutBadge from={1000 * 60 * 5.1} className="self-center" />
        <BaseModalTitle title="Still there?" />
        <BaseModalDescription description="Sorry, you'll be logged out and you will lose your changes unless you keep this window active." />
      </div>

      <div className="flex flex-col w-full gap-2">
        <ModalButton
          text="Stay Active"
          onClick={() => console.log("Stay Active")}
          className="bg-[#4465DB]"
        />
        <ModalButton
          text="Logout and Lose Changes"
          onClick={() => console.log("Stay Active")}
          className="bg-danger"
        />
      </div>
    </ModalBody>
  );
}

export default InactivityModal;
