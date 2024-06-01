import React from "react";
import "../../css/welcome.css";  // Importing the CSS file

export function Welcome() {
  return (
    <div className="text-white">
      <div className="welcome-container">
        <img src="img/logo.png" className="welcome-logo" />
        <p className="welcome-text">
          Welcome to OpenDevin, an open-source project aiming to replicate
          Devin, an autonomous AI software engineer who is capable of executing
          complex engineering tasks and collaborating actively with users on
          software development projects. This project aspires to replicate,
          enhance, and innovate upon Devin through the power of the open-source
          community.
        </p>
      </div>
    </div>
  );
}
