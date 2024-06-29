import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";

interface ErrorsProps {
  error?: Error | null;
}

function Errors({ error }: ErrorsProps): JSX.Element {
  const reduxErrors = useSelector((state: RootState) => state.errors.errors);

  const allErrors = error ? [error.message, ...reduxErrors] : reduxErrors;

  return (
    <div className="fixed left-1/2 transform -translate-x-1/2 top-4 z-50">
      {allErrors.map((errMsg, index) => (
        <div
          key={index}
          className="bg-red-800 dark:bg-red-900 text-white p-3 rounded-md shadow-md mb-2 text-sm"
        >
          ERROR: {errMsg}
        </div>
      ))}
    </div>
  );
}

export default Errors;
