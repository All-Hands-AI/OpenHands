import React, { useRef } from "react";
import { useSelector } from "react-redux";
import SyntaxHighlighter from "react-syntax-highlighter";
import Markdown from "react-markdown";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { VscArrowDown } from "react-icons/vsc";
import { useTranslation } from "react-i18next";
import { RootState } from "#/store";
import { ActionSecurityRisk } from "#/state/invariantSlice";
import { useScrollToBottom } from "#/hooks/useScrollToBottom";
import { I18nKey } from "#/i18n/declaration";
import { Invariant } from "#/state/invariantSlice";


function SecurityInvariant(): JSX.Element {
  const { t } = useTranslation();
  const { logs } = useSelector((state: RootState) => state.invariant);

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
        return t('securityRisk.low', { defaultValue: 'Low Risk' });
      case ActionSecurityRisk.MEDIUM:
        return t('securityRisk.medium', { defaultValue: 'Medium Risk' });
      case ActionSecurityRisk.HIGH:
        return t('securityRisk.high', { defaultValue: 'High Risk' });
      case ActionSecurityRisk.UNKNOWN:
      default:
        return t('securityRisk.unknown', { defaultValue: 'Unknown Risk' });
    }
  };

  return (
    <div className="flex-1 p-4 overflow-auto max-h-screen" ref={logsRef}>
      {logs.map((log: Invariant, index: number) => (
        <div key={index} className={`mb-2 p-2 rounded-lg`} style={{ backgroundColor: 'rgba(128, 128, 128, 0.2)' }}>
          <p className="text-sm">{log.content}{log.requires_confirmation && (
            <span className="text-red-500"> ({t(I18nKey.CHAT_INTERFACE$AGENT_AWAITING_USER_CONFIRMATION_MESSAGE)})</span>
          )}</p>
          <p className={`text-xs ${getRiskColor(log.security_risk)}`}>
            {getRiskText(log.security_risk)}
          </p>
        </div>
      ))}
    </div>
  );
}


export default SecurityInvariant;
