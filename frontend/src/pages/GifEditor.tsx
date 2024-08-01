import { useDisclosure } from "@nextui-org/react";
import React, { useState, useEffect } from "react";
import { useSelector } from "react-redux";
import { Toaster } from "react-hot-toast";
import ChatInterface from "#/components/chat/ChatInterface";
import Errors from "#/components/Errors";
import { Container, Orientation } from "#/components/Resizable";
import Workspace from "#/components/Workspace";
import LoadPreviousSessionModal from "#/components/modals/load-previous-session/LoadPreviousSessionModal";
import SettingsModal from "#/components/modals/settings/SettingsModal";
import Controls from "#/components/Controls";
import Terminal from "#/components/terminal/Terminal";
import Session from "#/services/session";
import { getToken } from "#/services/auth";
import { settingsAreUpToDate } from "#/services/settings";
import { readFile } from "#/services/fileService";

// React.StrictMode will cause double rendering, use this to prevent it
let initOnce = false;

function GifEditor(): JSX.Element {
  /* FIXME: all the below is duplicated from Main.tsx, should be refactored */
  const {
    isOpen: settingsModalIsOpen,
    onOpen: onSettingsModalOpen,
    onOpenChange: onSettingsModalOpenChange,
  } = useDisclosure();

  const {
    isOpen: loadPreviousSessionModalIsOpen,
    onOpen: onLoadPreviousSessionModalOpen,
    onOpenChange: onLoadPreviousSessionModalOpenChange,
  } = useDisclosure();

  useEffect(() => {
    if (initOnce) return;
    initOnce = true;

    if (!settingsAreUpToDate()) {
      onSettingsModalOpen();
    /*
     * FIXME: how should we do sessions with custom UIs?
     * } else if (getToken()) {
      onLoadPreviousSessionModalOpen();*/
    } else {
      Session.startNewSession();
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  /* FIXME: all the above is duplicated from Main.tsx, should be refactored */

  const [imageContent, setImageContent] = useState(null);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  async function blobToBase64(blob) {
    return new Promise((resolve, _) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  }

  useEffect(() => {
    readFile("dance.gif").then((file) => {
      return blobToBase64(file);
    }).then((base64) => {
      setImageContent(base64);
    }).catch((err) => {
      console.log(err);
    });
  }, [curAgentState]);

  return (
    <div className="h-screen w-screen flex flex-col">
      <div className="flex grow bg-neutral-900 text-white min-h-0">
        <Container
          orientation={Orientation.HORIZONTAL}
          className="grow h-full min-h-0 min-w-0 px-3 pt-3"
          initialSize={500}
          firstChild={<ChatInterface />}
          firstClassName="min-w-[500px] rounded-xl overflow-hidden border border-neutral-600"
          secondChild={
            <>
              <h1>Gif Editor</h1>
              { imageContent && (
                <img src={imageContent} alt="dance" className="max-h-full max-w-full" />
              ) }
            </>
          }
          secondClassName="grow"
        />
      </div>
      <Controls setSettingOpen={onSettingsModalOpen} />
      <SettingsModal
        isOpen={settingsModalIsOpen}
        onOpenChange={onSettingsModalOpenChange}
      />
      <LoadPreviousSessionModal
        isOpen={loadPreviousSessionModalIsOpen}
        onOpenChange={onLoadPreviousSessionModalOpenChange}
      />
      <Errors />
      <Toaster />
    </div>
  );
}

export default GifEditor;
