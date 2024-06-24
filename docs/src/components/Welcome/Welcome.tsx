import "../../css/welcome.css";
import Translate from '@docusaurus/Translate';

export function Welcome() {
  return (
    <div className="text-white">
      <div className="welcome-container">
        <img src="img/logo.png" className="welcome-logo" />
        <p className="welcome-text">
          <Translate id="welcome.message">
          Welcome to OpenDevin, an open-source autonomous AI software engineer
          that is capable of executing
          complex engineering tasks and collaborating actively with users on
          software development projects.
          </Translate>
        </p>
      </div>
    </div>
  );
}
