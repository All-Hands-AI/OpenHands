import Editor, { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import React from "react";
import TreeView, { flattenTree } from "react-accessible-treeview";
import { DiJavascript } from "react-icons/di";
import {
  FaCss3,
  FaFile,
  FaFolder,
  FaFolderOpen,
  FaHtml5,
  FaList,
  FaMarkdown,
  FaNpm,
  FaPython,
} from "react-icons/fa";
import { VscClose, VscListTree, VscRefresh } from "react-icons/vsc";
import { useSelector } from "react-redux";
import {
  sendRefreshFilesMessage,
  sendSelectedMessage,
} from "../services/fileService";
import { toggleExplorer } from "../state/codeSlice";
import store, { RootState } from "../store";

interface FileIconProps {
  filename: string;
}

function FileIcon({ filename }: FileIconProps): JSX.Element | null {
  const extension = filename.slice(filename.lastIndexOf(".") + 1);
  switch (extension) {
    case "js":
      return <DiJavascript />;
    case "ts":
      return <DiJavascript />;
    case "py":
      return <FaPython />;
    case "css":
      return <FaCss3 />;
    case "json":
      return <FaList />;
    case "npmignore":
      return <FaNpm />;
    case "html":
      return <FaHtml5 />;
    case "md":
      return <FaMarkdown />;
    default:
      return <FaFile />;
  }
}

interface FolderIconProps {
  isOpen: boolean;
}

function FolderIcon({ isOpen }: FolderIconProps): JSX.Element {
  return isOpen ? (
    <FaFolderOpen color="D9D3D0" className="icon" />
  ) : (
    <FaFolder color="D9D3D0" className="icon" />
  );
}

function Files(): JSX.Element | null {
  const folder = useSelector((state: RootState) => state.code.files);
  const selectedIds = useSelector((state: RootState) => state.code.selectedIds);
  const explorerOpen = useSelector(
    (state: RootState) => state.code.explorerOpen,
  );
  const data = flattenTree(folder);

  if (data.length <= 1) {
    return null;
  }
  if (!explorerOpen) {
    return (
      <div className="h-full bg-bg-workspace border-r-1 flex flex-col">
        <div className="flex gap-1 border-b-1 p-1 justify-end">
          <VscListTree
            className="cursor-pointer"
            onClick={() => store.dispatch(toggleExplorer())}
          />
        </div>
      </div>
    );
  }
  return (
    <div className="min-w-[250px] h-full bg-bg-workspace border-r-1 flex flex-col">
      <div className="flex gap-1 border-b-1 p-1 justify-end">
        <VscRefresh
          onClick={() => sendRefreshFilesMessage()}
          className="cursor-pointer"
        />
        <VscClose
          className="cursor-pointer"
          onClick={() => store.dispatch(toggleExplorer())}
        />
      </div>
      <div className="w-full overflow-x-auto h-full py-2">
        <TreeView
          className="font-mono text-sm"
          data={data}
          selectedIds={selectedIds}
          expandedIds={data.map((node) => node.id)}
          onNodeSelect={(node) => {
            if (!node.isBranch) {
              let fullPath = node.element.name;
              let currentNode = data.find(
                (file) => file.id === node.element.id,
              );
              while (currentNode && currentNode.parent) {
                currentNode = data.find(
                  (file) => file.id === node.element.parent,
                );
                fullPath = `${currentNode!.name}/${fullPath}`;
              }
              sendSelectedMessage(fullPath);
            }
          }}
          // eslint-disable-next-line react/no-unstable-nested-components
          nodeRenderer={({
            element,
            isBranch,
            isExpanded,
            getNodeProps,
            level,
          }) => (
            <div
              // eslint-disable-next-line react/jsx-props-no-spreading
              {...getNodeProps()}
              style={{ paddingLeft: 20 * (level - 1) }}
              className="cursor-pointer nowrap flex items-center gap-2 aria-selected:bg-slate-500 hover:bg-slate-700"
            >
              <div className="shrink-0">
                {isBranch ? (
                  <FolderIcon isOpen={isExpanded} />
                ) : (
                  <FileIcon filename={element.name} />
                )}
              </div>
              {element.name}
            </div>
          )}
        />
      </div>
    </div>
  );
}

function CodeEditor(): JSX.Element {
  const code = useSelector((state: RootState) => state.code.code);

  const bgColor = getComputedStyle(document.documentElement)
    .getPropertyValue("--bg-workspace")
    .trim();

  const handleEditorDidMount = (
    editor: editor.IStandaloneCodeEditor,
    monaco: Monaco,
  ) => {
    // 定义一个自定义主题
    monaco.editor.defineTheme("my-theme", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": bgColor,
      },
    });

    // 应用自定义主题
    monaco.editor.setTheme("my-theme");
  };

  return (
    <div className="w-full h-full bg-bg-workspace flex">
      <Files />
      <Editor
        height="95%"
        theme="vs-dark"
        defaultLanguage="python"
        defaultValue="# Welcome to OpenDevin!"
        value={code}
        onMount={handleEditorDidMount}
      />
    </div>
  );
}

export default CodeEditor;
