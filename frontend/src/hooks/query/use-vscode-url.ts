import { useQuery } from "@tanstack/react-query";
import React from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import toast from "#/utils/toast";
import { addAssistantMessage } from "#/state/chat-slice";
import { I18nKey } from "#/i18n/declaration";
import OpenHands from "#/api/open-hands";

export const useVSCodeUrl = () => {
  const { t } = useTranslation();
  const dispatch = useDispatch();

  const data = useQuery({
    queryKey: ["vscode_url"],
    queryFn: OpenHands.getVSCodeUrl,
    enabled: false,
  });

  const { data: vscodeUrlObject, isFetching } = data;

  React.useEffect(() => {
    if (isFetching) return;

    if (vscodeUrlObject?.vscode_url) {
      dispatch(
        addAssistantMessage(
          "You opened VS Code. Please inform the agent of any changes you made to the workspace or environment. To avoid conflicts, it's best to pause the agent before making any changes.",
        ),
      );
      window.open(vscodeUrlObject.vscode_url, "_blank");
    } else if (vscodeUrlObject?.error) {
      toast.error(
        `open-vscode-error-${new Date().getTime()}`,
        t(I18nKey.EXPLORER$VSCODE_SWITCHING_ERROR_MESSAGE, {
          error: vscodeUrlObject.error,
        }),
      );
    }
  }, [vscodeUrlObject, isFetching]);

  return data;
};
