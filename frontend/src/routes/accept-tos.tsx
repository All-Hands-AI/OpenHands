import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useNavigate } from "react-router";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { BrandButton } from "#/components/features/settings/brand-button";
import OpenHands from "#/api/open-hands";
import toast from "react-hot-toast";

export default function AcceptTOS() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAcceptTOS = async () => {
    try {
      setIsSubmitting(true);
      const success = await OpenHands.acceptTos();
      if (success) {
        toast.success("Terms of Service accepted");
        navigate("/");
      } else {
        toast.error("Failed to accept Terms of Service");
      }
    } catch (error) {
      console.error("Failed to accept TOS:", error);
      toast.error("Failed to accept Terms of Service");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background p-4">
      <div className="w-full max-w-md p-6 bg-card rounded-lg shadow-lg border border-tertiary">
        <div className="flex flex-col items-center gap-6">
          <AllHandsLogo width={68} height={46} />
          
          <h1 className="text-2xl font-bold text-center">
            Terms of Service
          </h1>
          
          <div className="text-sm text-muted-foreground mb-4">
            <p className="mb-4">
              Please read and accept our Terms of Service to continue using OpenHands.
            </p>
            <div className="border border-tertiary rounded-md p-4 max-h-60 overflow-y-auto mb-4">
              <p className="mb-2">
                By using OpenHands, you agree to the following terms:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>You will use the service responsibly and ethically</li>
                <li>You will not use the service for illegal activities</li>
                <li>You will not attempt to circumvent security measures</li>
                <li>You understand that your usage may be monitored</li>
                <li>You acknowledge that the service is provided as-is</li>
              </ul>
              <p className="mt-4">
                For the complete terms, please visit{" "}
                <a
                  href="https://www.all-hands.dev/tos"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline underline-offset-2 text-blue-500 hover:text-blue-700"
                >
                  {t(I18nKey.TOS$TERMS)}
                </a>
              </p>
            </div>
          </div>
          
          <BrandButton
            type="button"
            variant="primary"
            onClick={handleAcceptTOS}
            className="w-full"
            isDisabled={isSubmitting}
          >
            {isSubmitting ? "Processing..." : `${t(I18nKey.TOS$ACCEPT)} ${t(I18nKey.TOS$TERMS)}`}
          </BrandButton>
        </div>
      </div>
    </div>
  );
}