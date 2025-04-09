import { OpenHandsEventType } from "#/types/core/base";
import React from "react";
import {
  getDiffPath,
  getCommand,
  getCatFilePath,
  getUrlBrowser,
} from "./helpers";
import {
  FaEdit,
  FaTerminal,
  FaRegFileAlt,
  FaGlobe,
  FaPencilAlt,
  // FaTools,
} from "react-icons/fa";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { ol, ul } from "../markdown/list";

const MessageActionDisplay: React.FC<{
  messageActionID: string | undefined;
  content: string;
}> = ({ messageActionID, content }) => {
  const renderContent = () => {
    switch (messageActionID as OpenHandsEventType) {
      case "edit":
        return (
          <div className="items-center text-neutral-600 hover:opacity-70 gap-2 rounded-[15px] px-[10px] py-[3px] border border-neutral-300 inline-flex max-w-full bg-[#37352f10]">
            <div className="text-neutral-600 shrink-0">
              <FaEdit />
            </div>
            <div className="flex-1 max-w-[100%] text-ellipsis overflow-hidden whitespace-nowrap text-[13px]">
              Editing file: {getDiffPath(content)}
            </div>
          </div>
        );

      case "run":
      case "run_ipython":
        return (
          <div className="items-center text-neutral-600 hover:opacity-70 gap-2 rounded-[15px] px-[10px] py-[3px] border border-neutral-300 inline-flex max-w-full bg-[#37352f10]">
            <div className="text-neutral-600">
              <FaTerminal />
            </div>
            <div className="flex-1 max-w-[100%] text-ellipsis overflow-hidden whitespace-nowrap text-[13px]">
              Executing command: {getCommand(content)}
            </div>
          </div>
        );

      case "read":
        return (
          <div className="items-center text-neutral-600 hover:opacity-70 gap-2 rounded-[15px] px-[10px] py-[3px] border border-neutral-300 inline-flex max-w-full bg-[#37352f10]">
            <div className="text-neutral-600">
              <FaRegFileAlt />
            </div>
            <div className="flex-1 max-w-[100%] text-ellipsis overflow-hidden whitespace-nowrap text-[13px]">
              Reading file: {getCatFilePath(content)}
            </div>
          </div>
        );

      case "browse":
      case "browse_interactive":
        return (
          <div className="items-center text-neutral-600 hover:opacity-70 gap-2 rounded-[15px] px-[10px] py-[3px] border border-neutral-300 inline-flex max-w-full bg-[#37352f10]">
            <div className="text-neutral-600">
              <FaGlobe />
            </div>
            <div className="flex-1 max-w-[100%] text-ellipsis overflow-hidden whitespace-nowrap text-[13px]">
              Browsing: {getUrlBrowser(content)}
            </div>
          </div>
        );

      case "write":
        return (
          <div className="items-center text-neutral-600 hover:opacity-70 gap-2 rounded-[15px] px-[10px] py-[3px] border border-neutral-300 inline-flex max-w-full bg-[#37352f10]">
            <div className="text-neutral-600">
              <FaPencilAlt />
            </div>
            <div className="flex-1 max-w-[100%] text-ellipsis overflow-hidden whitespace-nowrap text-[13px]">
              Writing file: {getDiffPath(content)}
            </div>
          </div>
        );

      // case "mcp":
      // case "call_tool_mcp":
      // case "playwright_mcp_browser_screenshot":
      //   return (
      //     <div className="items-center hover:opacity-70 gap-2 rounded-[15px] px-[10px] py-[3px] border border-neutral-300 inline-flex max-w-full bg-[#37352f10]">
      //       <div className="text-neutral-600">
      //         <FaTools />
      //       </div>
      //       <div className="flex-1 max-w-[100%] text-ellipsis overflow-hidden whitespace-nowrap text-[13px]">
      //         Using tool: {content.split("\n")[0] || ""}
      //       </div>
      //     </div>
      //   );

      default:
        return (
          <Markdown
            components={{
              code,
              ul,
              ol,
            }}
            remarkPlugins={[remarkGfm]}
          >
            {content}
          </Markdown>
        );
    }
  };

  return <div className="mt-2">{renderContent()}</div>;
};

export default MessageActionDisplay;
