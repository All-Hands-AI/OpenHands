import React from "react";

function Planner(): JSX.Element {
  return (
    <div
      className="planner"
      style={{
        background: "black",
        padding: "1rem",
        height: "90%",
        margin: "1rem",
        borderRadius: "1rem",
      }}
    >
      <h3>
        Current Focus: Set up the development environment according to the
        project&apos;s instructions.
      </h3>
      <ul>
        <li>
          <input type="checkbox" checked readOnly />
          Clone the repository and review the README for project setup
          instructions.
        </li>
        <li>
          <input type="checkbox" checked readOnly />
          Identify the package manager and install necessary dependencies.
        </li>
        <li>
          <input type="checkbox" />
          Set up the development environment according to the project&apos;s
          instructions.
        </li>
        {/* Add more tasks */}
      </ul>
    </div>
  );
}

export default Planner;
