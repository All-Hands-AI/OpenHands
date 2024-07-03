import React, { useState, useRef } from "react";
import { useSelector } from "react-redux";
import SyntaxHighlighter from "react-syntax-highlighter";
import Markdown from "react-markdown";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { VscArrowDown } from "react-icons/vsc";
import { IoAlertCircle } from "react-icons/io5";
import { useTranslation } from "react-i18next";
import { RootState } from "#/store";
import { Tooltip } from "@nextui-org/react";
import { ActionSecurityRisk } from "#/state/invariantSlice";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import { I18nKey } from "#/i18n/declaration";
import { Invariant } from "#/state/invariantSlice";

type SectionType = 'logs' | 'policy' | 'settings';

function SecurityInvariant(): JSX.Element {
  const { t } = useTranslation();
  const { logs } = useSelector((state: RootState) => state.invariant);
  const [activeSection, setActiveSection] = useState('logs');

  const logsRef = useRef<HTMLDivElement>(null);

  useScrollToBottom(logsRef);

  const getRiskColor = (risk: ActionSecurityRisk) => {
    switch (risk) {
      case ActionSecurityRisk.LOW:
        return 'text-green-500';
      case ActionSecurityRisk.MEDIUM:
        return 'text-yellow-500';
      case ActionSecurityRisk.HIGH:
        return 'text-red-500';
      case ActionSecurityRisk.UNKNOWN:
      default:
        return 'text-gray-500';
    }
  };

  const getRiskText = (risk: ActionSecurityRisk) => {
    switch (risk) {
      case ActionSecurityRisk.LOW:
        return t('SECURITY_INVARIANT$LOW_RISK');
      case ActionSecurityRisk.MEDIUM:
        return t('SECURITY_INVARIANT$MEDIUM_RISK');
      case ActionSecurityRisk.HIGH:
        return t('SECURITY_INVARIANT$HIGH_RISK');
      case ActionSecurityRisk.UNKNOWN:
      default:
        return t('SECURITY_INVARIANT$UNKNOWN_RISK');
    }
  };

  const sections: { [key in SectionType]: JSX.Element } = {
    logs: (
      <div className="flex-1 p-4 max-h-screen">
        {logs.map((log: Invariant, index: number) => (
          <div key={index} className={`mb-2 p-2 rounded-lg ${log.confirmed_changed && log.is_confirmed === "confirmed" ? 'border-green-800' : log.confirmed_changed && log.is_confirmed === "rejected" ? 'border-red-800' : ''}`}
          style={{ backgroundColor: 'rgba(128, 128, 128, 0.2)', borderWidth: log.confirmed_changed ? '2px' : '0' }}>
              <p className="text-sm relative break-words">
                {log.content}
                {(log.is_confirmed === "awaiting_confirmation" || log.confirmed_changed) && (
                  <IoAlertCircle className="absolute top-0 right-0"></IoAlertCircle>
                )}
              </p>
            <p className={`text-xs ${getRiskColor(log.security_risk)}`}>
              {getRiskText(log.security_risk)}
            </p>
          </div>
        ))}
      </div>
    ),
    policy: (
      <div className="flex-1 p-4 max-h-screen">
        <h2 className="text-2xl mb-4">Policy</h2>
        <p>Policy content goes here.</p>
      </div>
    ),
    settings: (
      <div className="flex-1 p-4 max-h-screen">
        <h2 className="text-2xl mb-4">Settings</h2>
        <p>Settings content goes here.</p>
      </div>
    ),
  };

  return (
    <div className="flex w-full">
      <div className="w-60 bg-neutral-800 border-r border-r-neutral-600 p-4 flex-shrink-0">
        <b>Invariant Analyzer</b>
        <p style={{fontSize:"10px"}}>Invariant Analyzer continuously monitors your OpenDevin agent for security issues. <a className="underline" href="https://github.com/invariantlabs-ai/invariant" target="_blank">Click to learn more</a></p>
        <hr className="border-t border-neutral-600 my-2" />
        <ul className="space-y-2">
          <li
            className={`cursor-pointer p-2 rounded ${activeSection === 'logs' && 'bg-neutral-600'}`}
            onClick={() => setActiveSection('logs')}
          >
            Logs
          </li>
          <li
            className={`cursor-pointer p-2 rounded ${activeSection === 'policy' && 'bg-neutral-600'}`}
            onClick={() => setActiveSection('policy')}
          >
            Policy
          </li>
          <li
            className={`cursor-pointer p-2 rounded ${activeSection === 'settings' && 'bg-neutral-600'}`}
            onClick={() => setActiveSection('settings')}
          >
            Settings
          </li>
        </ul>
      </div>
      <div className="flex-1 p-4 bg-neutral-900 overflow-y-auto" ref={logsRef}>
        {sections[activeSection as SectionType]}
      </div>
    </div>
  );
}


export default SecurityInvariant;
