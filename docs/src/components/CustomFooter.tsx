import React from "react";
import { FaSlack, FaDiscord, FaGithub } from "react-icons/fa";
import "../css/footer.css"; // Importing the CSS file

function CustomFooter() {
  return (
    <footer className="custom-footer">
      <div className="footer-content">
        <div className="footer-top">
          <div className="footer-title">OpenDevin</div>
          <div className="footer-link">
            <a href="/modules/usage/intro">Docs</a>
          </div>
        </div>
        <div className="footer-community">Community</div>
        <div className="footer-icons">
          <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2jsrl32uf-fTeeFjNyNYxqSZt5NPY3fA" target="_blank" rel="noopener noreferrer">
            <FaSlack />
          </a>
          <a href="https://discord.gg/ESHStjSjD4" target="_blank" rel="noopener noreferrer">
            <FaDiscord />
          </a>
          <a href="https://github.com/OpenDevin/OpenDevin" target="_blank" rel="noopener noreferrer">
            <FaGithub />
          </a>
        </div>
        <div className="footer-bottom">
          <p>Copyright &copy; {new Date().getFullYear()} OpenDevin</p>
        </div>
      </div>
    </footer>
  );
}

export default CustomFooter;
