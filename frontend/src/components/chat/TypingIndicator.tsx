import React from "react";
import styles from "./TypingIndicator.module.css";

function TypingIndicator(): React.ReactElement {
  return (
    <div className="flex items-center space-x-1.5 bg-neutral-700 px-3 py-1.5 rounded-full">
      <span className={`w-1.5 h-1.5 bg-gray-400 rounded-full ${styles.dot}`} />
      <span className={`w-1.5 h-1.5 bg-gray-400 rounded-full ${styles.dot}`} />
      <span className={`w-1.5 h-1.5 bg-gray-400 rounded-full ${styles.dot}`} />
    </div>
  );
}

export default TypingIndicator;
