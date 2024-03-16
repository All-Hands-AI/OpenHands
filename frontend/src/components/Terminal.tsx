import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const Terminal: React.FC = () => {
  const terminalOutput = `> chatbot-ui@2.0.0 prepare
> husky install

husky - Git hooks installed

added 1455 packages, and audited 1456 packages in 1m

295 packages are looking for funding
  run \`npm fund\` for details
  
found 0 vulnerabilities
npm notice
npm notice New minor version of npm available! 10.7.3 -> 10.9.0
...`;

  return (
    <div className="terminal">
      <SyntaxHighlighter language="bash" style={atomDark}>
        {terminalOutput}
      </SyntaxHighlighter>
    </div>
  );
};

export default Terminal;