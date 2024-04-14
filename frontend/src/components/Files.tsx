import React, { useEffect } from "react";
import TreeView, { flattenTree } from "react-accessible-treeview";
import { AiOutlineFolder } from "react-icons/ai";
import { Accordion, AccordionItem, Button } from "@nextui-org/react";
import {
  TbLayoutSidebarLeftCollapseFilled,
  TbLayoutSidebarRightCollapseFilled,
} from "react-icons/tb";

import { IoIosArrowDown } from "react-icons/io";
import { VscRefresh } from "react-icons/vsc";
import { useSelector } from "react-redux";
import { getWorkspace, selectFile } from "../services/fileService";
import { setCode, updateWorkspace } from "../state/codeSlice";
import store, { RootState } from "../store";
import FolderIcon from "./FolderIcon";
import FileIcon from "./FileIcons";

interface FilesProps {
  setSelectedFileName: React.Dispatch<React.SetStateAction<string>>;
  setExplorerOpen: React.Dispatch<React.SetStateAction<boolean>>;
  explorerOpen: boolean;
}

function Files({
  setSelectedFileName,
  setExplorerOpen,
  explorerOpen,
}: FilesProps): JSX.Element {
  const workspaceFolder = useSelector(
    (state: RootState) => state.code.workspaceFolder,
  );

  const selectedIds = useSelector((state: RootState) => state.code.selectedIds);
  const workspaceTree = flattenTree(workspaceFolder);

  useEffect(() => {
    getWorkspace().then((file) => store.dispatch(updateWorkspace(file)));
  }, []);

  if (workspaceTree.length <= 1) {
    <div className="h-full bg-neutral-700 border-neutral-600 items-center border-r-1 flex flex-col">
      <div>No workspace found</div>
    </div>;
  }

  if (!explorerOpen) {
    return (
      <div className="h-full bg-neutral-800 border-neutral-600 items-center border-r-1 flex flex-col">
        <div className="flex mt-2 p-1 justify-end">
          <TbLayoutSidebarRightCollapseFilled
            className="cursor-pointer"
            onClick={() => setExplorerOpen(true)}
          />
        </div>
      </div>
    );
  }
  return (
    <div className="bg-neutral-800 h-full border-r-1 border-r-neutral-600 flex flex-col">
      <div className="flex p-2 items-center justify-between ">
        <Accordion className="px-0" defaultExpandedKeys={["1"]} isCompact>
          <AccordionItem
            classNames={{
              title: "editor-accordion-title",
              content: "editor-accordion-content",
            }}
            hideIndicator
            key="1"
            aria-label={workspaceFolder.name}
            title={
              <div className="group flex items-center justify-between ">
                <span className="text-neutral-400">{workspaceFolder.name}</span>
                <div className="opacity-0 translate-y-[10px] transition-all ease-in-out  group-hover:opacity-100 transform group-hover:-translate-y-0 ">
                  <Button
                    type="button"
                    style={{
                      width: "24px",
                      height: "24px",
                    }}
                    variant="flat"
                    onClick={() =>
                      getWorkspace().then((file) =>
                        store.dispatch(updateWorkspace(file)),
                      )
                    }
                    className="cursor-pointer text-[12px] bg-neutral-800"
                    isIconOnly
                    aria-label="Refresh"
                  >
                    <VscRefresh />
                  </Button>
                  <Button
                    type="button"
                    style={{
                      width: "24px",
                      height: "24px",
                    }}
                    variant="flat"
                    onClick={() => setExplorerOpen(false)}
                    className="cursor-pointer text-[12px]  bg-neutral-800"
                    isIconOnly
                    aria-label="Refresh"
                  >
                    <TbLayoutSidebarLeftCollapseFilled />
                  </Button>
                </div>
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
            <div className="w-full overflow-x-auto h-full py-2">
              <TreeView
                className="font-mono text-sm text-neutral-400"
                data={workspaceTree}
                selectedIds={selectedIds}
                expandedIds={workspaceTree.map((node) => node.id)}
                onNodeSelect={(node) => {
                  if (!node.isBranch) {
                    let fullPath = node.element.name;
                    setSelectedFileName(fullPath);
                    let currentNode = workspaceTree.find(
                      (file) => file.id === node.element.id,
                    );
                    while (currentNode !== undefined && currentNode.parent) {
                      currentNode = workspaceTree.find(
                        (file) => file.id === node.element.parent,
                      );
                      fullPath = `${currentNode!.name}/${fullPath}`;
                    }
                    selectFile(fullPath).then((code) => {
                      store.dispatch(setCode(code));
                    });
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
                    className="cursor-pointer rounded-[5px] p-1 nowrap flex items-center gap-2 aria-selected:bg-neutral-600 aria-selected:text-neutral-50 hover:text-neutral-50"
                  >
                    <div className="shrink-0 pl-5">
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
      </div>
    </div>
  );
}

export default Files;
