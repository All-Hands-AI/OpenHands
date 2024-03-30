import React from "react";

function Planner(): JSX.Element {
  return (
    <div className="h-full w-full bg-bg-workspace">
      <h3>
        Current Focus: Set up the development environment according to the
        project&apos;s instructions.
      </h3>
      <ul className="ml-4 mt-3">
        <li className="space-x-2">
          <input type="checkbox" checked readOnly />
          <span>
            Clone the repository and review the README for project setup
            instructions.
          </span>
        </li>
        <li className="space-x-2">
          <input type="checkbox" checked readOnly />
          <span>
            Identify the package manager and install necessary dependencies.
          </span>
        </li>
        <li className="space-x-2">
          <input type="checkbox" />
          <span>
            Set up the development environment according to the project&apos;s
            instructions.
          </span>
        </li>
        {/* Add more tasks */}
      </ul>
    </div>
  );
}

export default Planner;
