import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "#/components/ui/dialog";
import { Button } from "#/components/ui/button";
import { useTranslation } from "react-i18next";
import { useSettings } from "#/hooks/query/use-settings";
import OpenHands from "#/api/open-hands";
import { useQueryClient } from "@tanstack/react-query";

export function TermsOfServiceDialog() {
  const { t } = useTranslation();
  const { data: settings } = useSettings();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = React.useState(!settings?.ACCEPT_TOS);

  const handleAccept = async () => {
    await OpenHands.saveSettings({ accept_tos: true });
    await queryClient.invalidateQueries({ queryKey: ["settings"] });
    setIsOpen(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t("terms_of_service.title")}</DialogTitle>
          <DialogDescription>
            {t("terms_of_service.description")}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="terms-content max-h-[300px] overflow-y-auto">
            {t("terms_of_service.content")}
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" onClick={handleAccept}>
            {t("terms_of_service.accept")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}