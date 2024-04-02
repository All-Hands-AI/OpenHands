import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "../store";
import "./css/Errors.css";

function Errors(): JSX.Element {
  const errors = useSelector((state: RootState) => state.errors.errors);

  return (
    <div className="errors">
      {errors.map((error, index) => (
        <div key={index} className="error">
          ERROR: {error}
        </div>
      ))}
    </div>
  );
}

export default Errors;
