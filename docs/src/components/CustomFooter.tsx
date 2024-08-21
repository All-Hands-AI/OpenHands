import React from "react";
import { FaSlack, FaDiscord, FaGithub } from "react-icons/fa";
import Translate from '@docusaurus/Translate';
import "../css/footer.css";

function CustomFooter() {
  return (
    <footer className="custom-footer">
      <div className="footer-content">
        <div className="footer-top">
          <div className="footer-title">
            <Translate id="footer.title">OpenHands</Translate>
          </div>
          <div className="footer-link">
            <a href="/modules/usage/intro">
              <Translate id="footer.docs">Docs</Translate>
            </a>
          </div>
        </div>

        <div className="footer-icons">
          <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA" target="_blank" rel="noopener noreferrer">
            <FaSlack />
          </a>
          <a href="https://discord.gg/ESHStjSjD4" target="_blank" rel="noopener noreferrer">
            <FaDiscord />
          </a>
          <a href="https://github.com/All-Hands-AI/OpenHands" target="_blank" rel="noopener noreferrer">
            <FaGithub />
          </a>
        </div>
        <div className="footer-bottom">
          <p>
            <Translate id="footer.copyright" values={{ year: new Date().getFullYear() }}>
              {'Copyright © {year} OpenHands'}
            </Translate>
          </p>
        </div>
      </div>
    </footer>
  );
}

export default CustomFooter;
