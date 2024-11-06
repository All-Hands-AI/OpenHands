import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";

interface ErrorMessageProps {
  id?: string;
  message: string;
}

export function ErrorMessage({ id, message }: ErrorMessageProps) {
  const { t, i18n } = useTranslation();
  const [showDetails, setShowDetails] = useState(true);
  const [headline, setHeadline] = useState("");
  const [details, setDetails] = useState(message);

  useEffect(() => {
    if (id && i18n.exists(id)) {
      setHeadline(t(id));
      setDetails(message);
      setShowDetails(false);
    }
  }, [id, message, i18n.language]);

  return (
    <div className="flex gap-2 items-center justify-start border-l-2 border-danger pl-2 my-2 py-2">
      <div className="text-sm leading-4 flex flex-col gap-2">
        {headline && <p className="text-danger font-bold">{headline}</p>}
        {headline && (
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="cursor-pointer text-left"
          >
            {showDetails
              ? t("ERROR_MESSAGE$HIDE_DETAILS")
              : t("ERROR_MESSAGE$SHOW_DETAILS")}
          </button>
        )}
        {showDetails && <p className="text-neutral-300">{details}</p>}
      </div>
    </div>
  );
}
