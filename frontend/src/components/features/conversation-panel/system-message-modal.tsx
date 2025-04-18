import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { BaseModalTitle } from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { cn } from "#/utils/utils";
import { ChevronDown, ChevronRight } from "lucide-react";
import { JsonView } from 'react-json-view-lite';
import 'react-json-view-lite/dist/index.css';

// Custom JSON viewer styles that match our application theme
const customJsonStyles = {
  container: "bg-transparent",
  basicChildStyle: "text-gray-300",
  stringValue: "text-green-400",
  numberValue: "text-blue-400",
  booleanValue: "text-yellow-400",
  nullValue: "text-red-400",
  keyStyle: "text-primary font-semibold",
  arrowStyle: "text-gray-400",
  // Add more spacing for better readability
  itemMargin: "my-1",
  // Increase indentation for better hierarchy visualization
  indentSize: 20,
};

interface SystemMessageModalProps {
  isOpen: boolean;
  onClose: () => void;
  systemMessage: {
    content: string;
    tools: Array<Record<string, unknown>> | null;
    openhands_version: string | null;
    agent_class: string | null;
  } | null;
}

interface FunctionData {
  name?: string;
  description?: string;
  parameters?: Record<string, unknown>;
}

interface ToolData {
  type?: string;
  function?: FunctionData;
  name?: string;
  description?: string;
  parameters?: Record<string, unknown>;
}

export function SystemMessageModal({
  isOpen,
  onClose,
  systemMessage,
}: SystemMessageModalProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<"system" | "tools">("system");
  const [expandedTools, setExpandedTools] = useState<Record<number, boolean>>({});

  if (!systemMessage) {
    return null;
  }
  
  const toggleTool = (index: number) => {
    setExpandedTools(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  return (
    isOpen && (
      <>
        <ModalBackdrop onClose={onClose}>
          <ModalBody width="medium" className="max-h-[80vh] flex flex-col items-start">
          <div className="flex flex-col gap-6 w-full">
            <BaseModalTitle title={t("SYSTEM_MESSAGE_MODAL$TITLE")} />
            <div className="flex flex-col gap-2">
              {systemMessage.agent_class && (
                <div className="text-sm">
                  <span className="font-semibold text-gray-300">{t("SYSTEM_MESSAGE_MODAL$AGENT_CLASS")}</span>{" "}
                  <span className="font-medium text-primary">{systemMessage.agent_class}</span>
                </div>
              )}
              {systemMessage.openhands_version && (
                <div className="text-sm">
                  <span className="font-semibold text-gray-300">{t("SYSTEM_MESSAGE_MODAL$OPENHANDS_VERSION")}</span>{" "}
                  <span className="text-gray-100 text-primary">{systemMessage.openhands_version}</span>
                </div>
              )}
            </div>
          </div>

          <div className="w-full">
            <div className="flex border-b mb-2">
              <button
                type="button"
                className={cn(
                  "px-4 py-2 font-medium border-b-2 transition-colors",
                  activeTab === "system" 
                    ? "border-primary text-primary" 
                    : "border-transparent hover:text-gray-700 dark:hover:text-gray-300"
                )}
                onClick={() => setActiveTab("system")}
              >
                {t("SYSTEM_MESSAGE_MODAL$SYSTEM_MESSAGE_TAB")}
              </button>
              {systemMessage.tools && systemMessage.tools.length > 0 && (
                <button
                  type="button"
                  className={cn(
                    "px-4 py-2 font-medium border-b-2 transition-colors",
                    activeTab === "tools" 
                      ? "border-primary text-primary" 
                      : "border-transparent hover:text-gray-700 dark:hover:text-gray-300"
                  )}
                  onClick={() => setActiveTab("tools")}
                >
                  {t("SYSTEM_MESSAGE_MODAL$TOOLS_TAB")}
                </button>
              )}
            </div>

            <div className="h-[60vh] overflow-auto rounded-md border border-gray-700 bg-gray-900">
              {activeTab === "system" && (
                <div className="p-5 whitespace-pre-wrap font-mono text-sm leading-relaxed bg-gray-900 text-gray-300">
                  {systemMessage.content}
                </div>
              )}

              {activeTab === "tools" && systemMessage.tools && systemMessage.tools.length > 0 && (
                <div className="p-4 space-y-4">
                  {systemMessage.tools.map((tool, index) => {
                    // Extract function data from the nested structure
                    const toolData = tool as ToolData;
                    const functionData = toolData.function || toolData;
                    const name = functionData.name || (toolData.type === "function" && toolData.function?.name) || "";
                    const description = functionData.description || (toolData.type === "function" && toolData.function?.description) || "";
                    const parameters = functionData.parameters || (toolData.type === "function" && toolData.function?.parameters) || null;
                    
                    const isExpanded = expandedTools[index] || false;
                    
                    return (
                      <div key={index} className="border rounded-md bg-gray-800 border-gray-700 overflow-hidden">
                        <button 
                          onClick={() => toggleTool(index)}
                          className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-700 transition-colors"
                        >
                          <div className="flex items-center">
                            <span className="inline-block w-6 h-6 mr-2 rounded-full bg-primary/20 flex items-center justify-center">
                              <span className="text-primary text-xs font-bold">{index + 1}</span>
                            </span>
                            <h3 className="font-bold text-primary">{String(name)}</h3>
                          </div>
                          <span className="text-gray-300">
                            {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                          </span>
                        </button>
                        
                        {isExpanded && (
                          <div className="px-4 pb-4 pt-1">
                            <div className="mt-2 mb-4 p-3 bg-gray-800/50 rounded-md border border-gray-700/50">
                              <p className="text-sm whitespace-pre-wrap text-gray-300 leading-relaxed">
                                {String(description)}
                              </p>
                            </div>
                            
                            {/* Parameters section */}
                            {parameters && (
                              <div className="mt-3">
                                <h4 className="text-sm font-semibold text-gray-300">{t("SYSTEM_MESSAGE_MODAL$PARAMETERS")}</h4>
                                <div className="text-sm mt-2 p-4 bg-gray-900 rounded-md overflow-auto border border-gray-700 text-gray-300 max-h-[300px]">
                                  <JsonView 
                                    data={parameters}
                                    style={customJsonStyles}
                                    shouldExpandNode={() => true}
                                  />
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
              
              {activeTab === "tools" && (!systemMessage.tools || systemMessage.tools.length === 0) && (
                <div className="flex items-center justify-center h-full p-4">
                  <p className="text-gray-400">{t("SYSTEM_MESSAGE_MODAL$NO_TOOLS")}</p>
                </div>
              )}
            </div>
          </div>


        </ModalBody>
      </ModalBackdrop>
      </>
    )
  );
}
