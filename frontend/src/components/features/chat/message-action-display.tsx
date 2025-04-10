import { OpenHandsEventType } from "#/types/core/base"
import React from "react"
import {
  getDiffPath,
  getCommand,
  getCatFilePath,
  getUrlBrowser,
} from "./helpers"
import {
  FaEdit,
  FaTerminal,
  FaRegFileAlt,
  FaGlobe,
  FaPencilAlt,
  // FaTools,
} from "react-icons/fa"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { code } from "../markdown/code"
import { ol, ul } from "../markdown/list"
import store from "#/store"
import { setEventID } from "#/state/computer-slice"
import { setCurrentPathViewed } from "#/state/file-state-slice"

const actionWrapClassName =
  "inline-flex max-w-full items-center gap-2 rounded-[15px] border border-neutral-1000 bg-[#37352f10] px-[10px] py-[3px] text-neutral-600 hover:opacity-70 dark:border-neutral-300 cursor-pointer"

const MessageActionDisplay: React.FC<{
  messageActionID: string | undefined
  content: string
  eventID?: number
}> = ({ messageActionID, content, eventID }) => {
  const openComputertByEventID = (eventID) => {
    if (typeof eventID === "number") {
      store.dispatch(setCurrentPathViewed(""))
      store.dispatch(setEventID(eventID))
    }
  }

  const renderContent = () => {
    switch (messageActionID as OpenHandsEventType) {
      case "edit":
        return (
          <div
            className={actionWrapClassName}
            onClick={() => openComputertByEventID(eventID)}
          >
            <div className="shrink-0 text-neutral-600">
              <FaEdit />
            </div>
            <div className="max-w-[100%] flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-[13px]">
              Editing file: {getDiffPath(content)}
            </div>
          </div>
        )

      case "run":
      case "run_ipython":
        return (
          <div
            className={actionWrapClassName}
            onClick={() => openComputertByEventID(eventID)}
          >
            <div className="text-neutral-600">
              <FaTerminal />
            </div>
            <div className="max-w-[100%] flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-[13px]">
              Executing command: {getCommand(content)}
            </div>
          </div>
        )

      case "read":
        return (
          <div
            className={actionWrapClassName}
            onClick={() => openComputertByEventID(eventID)}
          >
            <div className="text-neutral-600">
              <FaRegFileAlt />
            </div>
            <div className="max-w-[100%] flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-[13px]">
              Reading file: {getCatFilePath(content)}
            </div>
          </div>
        )

      case "browse":
      case "browse_interactive":
        return (
          <div
            className={actionWrapClassName}
            onClick={() => openComputertByEventID(eventID)}
          >
            <div className="text-neutral-600">
              <FaGlobe />
            </div>
            <div className="max-w-[100%] flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-[13px]">
              Browsing: {getUrlBrowser(content)}
            </div>
          </div>
        )

      case "write":
        return (
          <div
            className={actionWrapClassName}
            onClick={() => openComputertByEventID(eventID)}
          >
            <div className="text-neutral-600">
              <FaPencilAlt />
            </div>
            <div className="max-w-[100%] flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-[13px]">
              Writing file: {getDiffPath(content)}
            </div>
          </div>
        )

      // case "mcp":
      // case "call_tool_mcp":
      // case "playwright_mcp_browser_screenshot":
      //   return (
      //     <div className="items-center hover:opacity-70 gap-2 rounded-[15px] px-[10px] py-[3px] border border-neutral-1000 dark:border-neutral-300 inline-flex max-w-full bg-[#37352f10]">
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
        )
    }
  }

  return <div className="mt-2 max-w-[500px]">{renderContent()}</div>
}

export default MessageActionDisplay
