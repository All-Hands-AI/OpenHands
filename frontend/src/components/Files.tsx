import { Accordion, AccordionItem } from "@nextui-org/react";
import React, { useEffect } from "react";
import TreeView, {
  ITreeViewOnExpandProps,
  ITreeViewOnNodeSelectProps,
} from "react-accessible-treeview";
import { AiOutlineFolder } from "react-icons/ai";

import {
  IoIosArrowBack,
  IoIosArrowDown,
  IoIosArrowForward,
  IoIosRefresh,
} from "react-icons/io";

import { useDispatch, useSelector } from "react-redux";
import { getWorkspaceDepthOne, selectFile } from "../services/fileService";
import {
  pruneWorkspace,
  resetWorkspace,
  setCode,
  updateWorkspace,
} from "../state/codeSlice";
import { RootState } from "../store";
import FileIcon from "./FileIcons";
import FolderIcon from "./FolderIcon";
import IconButton, { IconButtonProps } from "./IconButton";

interface FilesProps {
  setSelectedFileName: React.Dispatch<React.SetStateAction<string>>;
  setExplorerOpen: React.Dispatch<React.SetStateAction<boolean>>;
  explorerOpen: boolean;
}

function RefreshButton({
  onClick,
  ariaLabel,
}: Omit<IconButtonProps, "icon">): React.ReactElement {
  return (
    <IconButton
      icon={
        <IoIosRefresh
          size={20}
          className="text-neutral-400 hover:text-neutral-100 transition"
        />
      }
      onClick={onClick}
      ariaLabel={ariaLabel}
    />
  );
}

function CloseButton({
  onClick,
  ariaLabel,
}: Omit<IconButtonProps, "icon">): React.ReactElement {
  return (
    <IconButton
      icon={
        <IoIosArrowBack
          size={20}
          className="text-neutral-400 hover:text-neutral-100 transition"
        />
      }
      onClick={onClick}
      ariaLabel={ariaLabel}
    />
  );
}

function Files({
  setSelectedFileName,
  setExplorerOpen,
  explorerOpen,
}: FilesProps): JSX.Element {
  const dispatch = useDispatch();
  const workspaceTree = useSelector(
    (state: RootState) => state.code.workspaceFolder,
  );

  const selectedIds = useSelector((state: RootState) => state.code.selectedIds);

  useEffect(() => {
    getWorkspaceDepthOne("").then((file) => dispatch(updateWorkspace(file)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (workspaceTree.length <= 1) {
    <div className="h-full bg-neutral-700 border-neutral-600 items-center border-r-1 flex flex-col">
      <div>No workspace found</div>
    </div>;
  }

  if (!explorerOpen) {
    return (
      <div className="h-full min-w-[48px] bg-neutral-800 border-neutral-600 items-center border-r-1 flex flex-col transition-all ease-soft-spring">
        <div className="flex mt-2 p-2 justify-end">
          <IoIosArrowForward
            size={20}
            className="cursor-pointer text-neutral-600 hover:text-neutral-100 transition"
            onClick={() => setExplorerOpen(true)}
          />
        </div>
      </div>
    );
  }

  const handleNodeSelect = (node: ITreeViewOnNodeSelectProps) => {
    if (!node.element.isBranch) {
      let fullPath = node.element.name;
      setSelectedFileName(fullPath);
      let currentNode = workspaceTree.find(
        (file) => file.id === node.element.id,
      );
      while (currentNode !== undefined && currentNode.parent) {
        currentNode = workspaceTree.find(
          (file) => file.id === node.element.parent,
        );
        fullPath = `${currentNode?.name}/${fullPath}`;
      }
      selectFile(fullPath).then((code) => {
        dispatch(setCode(code));
      });
    }
  };

  const handleNodeExpand = (node: ITreeViewOnExpandProps) => {
    if (node.isExpanded) {
      const currentNode = workspaceTree.find(
        (treeNode) => treeNode.id === node.element.id,
      );
      if (!currentNode) return;
      getWorkspaceDepthOne(currentNode.relativePath).then((files) => {
        dispatch(updateWorkspace(files));
      });
    } else {
      const currentNode = workspaceTree.find(
        (treeNode) => treeNode.id === node.element.id,
      );
      dispatch(pruneWorkspace(currentNode));
    }
  };

  return (
    <div className="bg-neutral-800 min-w-[228px] h-full border-r-1 border-r-neutral-600 flex flex-col transition-all ease-soft-spring">
      <div className="flex p-2 items-center justify-between relative">
        <Accordion className="px-0" defaultExpandedKeys={["1"]} isCompact>
          <AccordionItem
            classNames={{
              title: "editor-accordion-title",
              content: "editor-accordion-content",
            }}
            hideIndicator
            key="1"
            aria-label=""
            title={
              <div className="group flex items-center justify-between">
                <span className="text-neutral-400 text-sm" />
              </div>
            }
            className="editor-accordion"
            startContent={
              <div className="flex items-center gap-1">
                <IoIosArrowDown className="text-neutral-400" />
                <AiOutlineFolder className="text-neutral-400" />
              </div>
            }
          >
            <div className="w-full overflow-x-auto h-full pt-[4px]">
              <TreeView
                className="text-sm text-neutral-400"
                data={workspaceTree}
                selectedIds={selectedIds}
                expandedIds={workspaceTree
                  .filter((node) => node.children.length > 0)
                  .map((node) => node.id)}
                onNodeSelect={handleNodeSelect}
                onExpand={handleNodeExpand}
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
                    className="cursor-pointer rounded-[5px] p-1 nowrap flex items-center gap-2 aria-selected:bg-neutral-600 aria-selected:text-white hover:text-white"
                  >
                    <div className="shrink-0 pl-[48px]">
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
          </AccordionItem>
        </Accordion>
        <div className="transform flex h-[24px] items-center gap-1 absolute top-2 right-2">
          <RefreshButton
            onClick={() => {
              dispatch(resetWorkspace());
              getWorkspaceDepthOne("").then((file) =>
                dispatch(updateWorkspace(file)),
              );
            }}
            ariaLabel="Refresh"
          />
          <CloseButton
            onClick={() => setExplorerOpen(false)}
            ariaLabel="Close Explorer"
          />
        </div>
      </div>
    </div>
  );
}

export default Files;
