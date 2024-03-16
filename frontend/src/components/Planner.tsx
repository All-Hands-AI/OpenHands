import React from 'react';

const Planner: React.FC = () => {
  return (
    <div className="planner">
      <h3>Current Focus: Set up the development environment according to the project's instructions.</h3>
      <ul>
        <li>
          <input type="checkbox" checked readOnly />
          Clone the repository and review the README for project setup instructions.
        </li>
        <li>
          <input type="checkbox" checked readOnly />
          Identify the package manager and install necessary dependencies.
        </li>
        <li>
          <input type="checkbox" />
          Set up the development environment according to the project's instructions.
        </li>
        {/* Add more tasks */}
      </ul>
    </div>
  );
};

export default Planner;
