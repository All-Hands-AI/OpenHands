import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "../store";

function Errors(): JSX.Element {
  const errors = useSelector((state: RootState) => state.errors.errors);

  return (
    <div className="fixed left-1/2 transform -translate-x-1/2 top-4 z-50">
      {errors.map((error, index) => (
        <div key={index} className="bg-red-800 p-4 rounded-md shadow-md mb-2">
          ERROR: {error}
        </div>
      ))}
    </div>
  );
}

export default Errors;
