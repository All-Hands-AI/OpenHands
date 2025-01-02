import React from "react";
import { useSelector } from "react-redux";
import { IoAlertCircle } from "react-icons/io5";
import { useTranslation } from "react-i18next";
import { Editor, Monaco } from "@monaco-editor/react";
import { editor } from "monaco-editor";
import { Button, Select, SelectItem } from "@nextui-org/react";
import { useMutation } from "@tanstack/react-query";
import { RootState } from "#/store";
import {
  ActionSecurityRisk,
  SecurityAnalyzerLog,
} from "#/state/security-analyzer-slice";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";
import { I18nKey } from "#/i18n/declaration";
import toast from "#/utils/toast";
import InvariantLogoIcon from "./assets/logo";
import { getFormattedDateTime } from "#/utils/gget-formatted-datetime";
import { downloadJSON } from "#/utils/download-json";
import InvariantService from "#/api/invariant-service";
import { useGetPolicy } from "#/hooks/query/use-get-policy";
import { useGetRiskSeverity } from "#/hooks/query/use-get-risk-severity";
import { useGetTraces } from "#/hooks/query/use-get-traces";

type SectionType = "logs" | "policy" | "settings";

function SecurityInvariant() {
  const { t } = useTranslation();
  const { logs } = useSelector((state: RootState) => state.securityAnalyzer);

  const [activeSection, setActiveSection] = React.useState("logs");
  const [policy, setPolicy] = React.useState("");
  const [selectedRisk, setSelectedRisk] = React.useState(
    ActionSecurityRisk.MEDIUM,
  );

  const logsRef = React.useRef<HTMLDivElement>(null);

  useGetPolicy({ onSuccess: setPolicy });

  useGetRiskSeverity({
    onSuccess: (riskSeverity) => {
      setSelectedRisk(
        riskSeverity === 0
          ? ActionSecurityRisk.LOW
          : riskSeverity || ActionSecurityRisk.MEDIUM,
      );
    },
  });

  const { refetch: exportTraces } = useGetTraces({
    onSuccess: (traces) => {
      toast.info(t(I18nKey.INVARIANT$TRACE_EXPORTED_MESSAGE));

      const filename = `openhands-trace-${getFormattedDateTime()}.json`;
      downloadJSON(traces, filename);
    },
  });

  const { mutate: updatePolicy } = useMutation({
    mutationFn: (variables: { policy: string }) =>
      InvariantService.updatePolicy(variables.policy),
    onSuccess: () => {
      toast.info(t(I18nKey.INVARIANT$POLICY_UPDATED_MESSAGE));
    },
  });

  const { mutate: updateRiskSeverity } = useMutation({
    mutationFn: (variables: { riskSeverity: number }) =>
      InvariantService.updateRiskSeverity(variables.riskSeverity),
    onSuccess: () => {
      toast.info(t(I18nKey.INVARIANT$SETTINGS_UPDATED_MESSAGE));
    },
  });

  useScrollToBottom(logsRef);

  const getRiskColor = React.useCallback((risk: ActionSecurityRisk) => {
    switch (risk) {
      case ActionSecurityRisk.LOW:
        return "text-green-500";
      case ActionSecurityRisk.MEDIUM:
        return "text-yellow-500";
      case ActionSecurityRisk.HIGH:
        return "text-red-500";
      case ActionSecurityRisk.UNKNOWN:
      default:
        return "text-gray-500";
    }
  }, []);

  const getRiskText = React.useCallback(
    (risk: ActionSecurityRisk) => {
      switch (risk) {
        case ActionSecurityRisk.LOW:
          return t(I18nKey.SECURITY_ANALYZER$LOW_RISK);
        case ActionSecurityRisk.MEDIUM:
          return t(I18nKey.SECURITY_ANALYZER$MEDIUM_RISK);
        case ActionSecurityRisk.HIGH:
          return t(I18nKey.SECURITY_ANALYZER$HIGH_RISK);
        case ActionSecurityRisk.UNKNOWN:
        default:
          return t(I18nKey.SECURITY_ANALYZER$UNKNOWN_RISK);
      }
    },
    [t],
  );

  const handleEditorDidMount = React.useCallback(
    (_: editor.IStandaloneCodeEditor, monaco: Monaco): void => {
      monaco.editor.defineTheme("my-theme", {
        base: "vs-dark",
        inherit: true,
        rules: [],
        colors: {
          "editor.background": "#171717",
        },
      });

      monaco.editor.setTheme("my-theme");
    },
    [],
  );

  const sections: Record<SectionType, React.ReactNode> = {
    logs: (
      <>
        <div className="flex justify-between items-center border-b border-neutral-600 mb-4 p-4">
          <h2 className="text-2xl">{t(I18nKey.INVARIANT$LOG_LABEL)}</h2>
          <Button onPress={() => exportTraces()} className="bg-neutral-700">
            {t(I18nKey.INVARIANT$EXPORT_TRACE_LABEL)}
          </Button>
        </div>
        <div className="flex-1 p-4 max-h-screen overflow-y-auto" ref={logsRef}>
          {logs.map((log: SecurityAnalyzerLog, index: number) => (
            <div
              key={index}
              className={`mb-2 p-2 rounded-lg ${log.confirmed_changed && log.confirmation_state === "confirmed" ? "border-green-800" : "border-red-800"}`}
              style={{
                backgroundColor: "rgba(128, 128, 128, 0.2)",
                borderWidth: log.confirmed_changed ? "2px" : "0",
              }}
            >
              <p className="text-sm relative break-words">
                {log.content}
                {(log.confirmation_state === "awaiting_confirmation" ||
                  log.confirmed_changed) && (
                  <IoAlertCircle className="absolute top-0 right-0" />
                )}
              </p>
              <p className={`text-xs ${getRiskColor(log.security_risk)}`}>
                {getRiskText(log.security_risk)}
              </p>
            </div>
          ))}
        </div>
      </>
    ),
    policy: (
      <>
        <div className="flex justify-between items-center border-b border-neutral-600 mb-4 p-4">
          <h2 className="text-2xl">{t(I18nKey.INVARIANT$POLICY_LABEL)}</h2>
          <Button
            className="bg-neutral-700"
            onPress={() => updatePolicy({ policy })}
          >
            {t(I18nKey.INVARIANT$UPDATE_POLICY_LABEL)}
          </Button>
        </div>
        <div className="flex grow items-center justify-center">
          <Editor
            path="policy.py"
            height="100%"
            onMount={handleEditorDidMount}
            value={policy}
            onChange={(value) => setPolicy(value || "")}
          />
        </div>
      </>
    ),
    settings: (
      <>
        <div className="flex justify-between items-center border-b border-neutral-600 mb-4 p-4">
          <h2 className="text-2xl">{t(I18nKey.INVARIANT$SETTINGS_LABEL)}</h2>
          <Button
            className="bg-neutral-700"
            onPress={() => updateRiskSeverity({ riskSeverity: selectedRisk })}
          >
            {t(I18nKey.INVARIANT$UPDATE_SETTINGS_LABEL)}
          </Button>
        </div>
        <div className="flex grow p-4">
          <div className="flex flex-col w-full">
            <p className="mb-2">
              {t(I18nKey.INVARIANT$ASK_CONFIRMATION_RISK_SEVERITY_LABEL)}
            </p>
            <Select
              placeholder="Select risk severity"
              value={selectedRisk}
              onChange={(e) =>
                setSelectedRisk(Number(e.target.value) as ActionSecurityRisk)
              }
              className={getRiskColor(selectedRisk)}
              selectedKeys={new Set([selectedRisk.toString()])}
              aria-label="Select risk severity"
            >
              <SelectItem
                key={ActionSecurityRisk.UNKNOWN}
                aria-label="Unknown Risk"
                className={getRiskColor(ActionSecurityRisk.UNKNOWN)}
              >
                {getRiskText(ActionSecurityRisk.UNKNOWN)}
              </SelectItem>
              <SelectItem
                key={ActionSecurityRisk.LOW}
                aria-label="Low Risk"
                className={getRiskColor(ActionSecurityRisk.LOW)}
              >
                {getRiskText(ActionSecurityRisk.LOW)}
              </SelectItem>
              <SelectItem
                key={ActionSecurityRisk.MEDIUM}
                aria-label="Medium Risk"
                className={getRiskColor(ActionSecurityRisk.MEDIUM)}
              >
                {getRiskText(ActionSecurityRisk.MEDIUM)}
              </SelectItem>
              <SelectItem
                key={ActionSecurityRisk.HIGH}
                aria-label="High Risk"
                className={getRiskColor(ActionSecurityRisk.HIGH)}
              >
                {getRiskText(ActionSecurityRisk.HIGH)}
              </SelectItem>
              <SelectItem
                key={ActionSecurityRisk.HIGH + 1}
                aria-label="Don't ask for confirmation"
              >
                {t(I18nKey.INVARIANT$DONT_ASK_FOR_CONFIRMATION_LABEL)}
              </SelectItem>
            </Select>
          </div>
        </div>
      </>
    ),
  };

  return (
    <div className="flex flex-1 w-full h-full">
      <div className="w-60 bg-neutral-800 border-r border-r-neutral-600 p-4 flex-shrink-0">
        <div className="text-center mb-2">
          <InvariantLogoIcon className="mx-auto mb-1" />
          <b>{t(I18nKey.INVARIANT$INVARIANT_ANALYZER_LABEL)}</b>
        </div>
        <p className="text-[0.6rem]">
          {t(I18nKey.INVARIANT$INVARIANT_ANALYZER_MESSAGE)}{" "}
          <a
            className="underline"
            href="https://github.com/invariantlabs-ai/invariant"
            target="_blank"
            rel="noreferrer"
          >
            {t(I18nKey.INVARIANT$CLICK_TO_LEARN_MORE_LABEL)}
          </a>
        </p>
        <hr className="border-t border-neutral-600 my-2" />
        <ul className="space-y-2">
          <div
            className={`cursor-pointer p-2 rounded ${activeSection === "logs" && "bg-neutral-600"}`}
            onClick={() => setActiveSection("logs")}
          >
            {t(I18nKey.INVARIANT$LOG_LABEL)}
          </div>
          <div
            className={`cursor-pointer p-2 rounded ${activeSection === "policy" && "bg-neutral-600"}`}
            onClick={() => setActiveSection("policy")}
          >
            {t(I18nKey.INVARIANT$POLICY_LABEL)}
          </div>
          <div
            className={`cursor-pointer p-2 rounded ${activeSection === "settings" && "bg-neutral-600"}`}
            onClick={() => setActiveSection("settings")}
          >
            {t(I18nKey.INVARIANT$SETTINGS_LABEL)}
          </div>
        </ul>
      </div>
      <div className="flex flex-col min-h-0 w-full overflow-y-auto bg-neutral-900">
        {sections[activeSection as SectionType]}
      </div>
    </div>
  );
}

export default SecurityInvariant;
