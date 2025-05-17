import React, { useEffect, useState } from "react";
import { useParams } from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { LoadingSpinner } from "#/components/shared/loading-spinner";

interface StatusField {
  title: string;
  value: string;
  isLoading: boolean;
  error: string | null;
}

interface StatusResponse {
  intent?: string;
  definition_of_done?: string;
  current_status?: string;
  error?: string;
}

export default function StatusTab() {
  const { t } = useTranslation();
  const { conversationId } = useParams<{ conversationId: string }>();

  const [intent, setIntent] = useState<StatusField>({
    title: t(I18nKey.STATUS$INTENT_TITLE),
    value: "",
    isLoading: true,
    error: null,
  });

  const [definitionOfDone, setDefinitionOfDone] = useState<StatusField>({
    title: t(I18nKey.STATUS$DEFINITION_OF_DONE_TITLE),
    value: "",
    isLoading: true,
    error: null,
  });

  const [currentStatus, setCurrentStatus] = useState<StatusField>({
    title: t(I18nKey.STATUS$CURRENT_STATUS_TITLE),
    value: "",
    isLoading: true,
    error: null,
  });

  const fetchStatusField = async (
    url: string,
    onSuccess: (data: StatusResponse) => void,
    onError: (error: string) => void,
  ) => {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      onSuccess(data);
    } catch (error) {
      // Log error but don't show console message in production
      if (process.env.NODE_ENV !== "production") {
        // eslint-disable-next-line no-console
        console.error(t(I18nKey.STATUS$ERROR_FETCHING), error);
      }
      onError(error instanceof Error ? error.message : String(error));
    }
  };

  useEffect(() => {
    if (!conversationId) return;

    // Fetch intent
    fetchStatusField(
      `/api/conversations/${conversationId}/status/intent`,
      (data) =>
        setIntent({
          ...intent,
          value: data.intent || "",
          isLoading: false,
          error: null,
        }),
      (error) =>
        setIntent({
          ...intent,
          isLoading: false,
          error,
        }),
    );

    // Fetch definition of done
    fetchStatusField(
      `/api/conversations/${conversationId}/status/definition-of-done`,
      (data) =>
        setDefinitionOfDone({
          ...definitionOfDone,
          value: data.definition_of_done || "",
          isLoading: false,
          error: null,
        }),
      (error) =>
        setDefinitionOfDone({
          ...definitionOfDone,
          isLoading: false,
          error,
        }),
    );

    // Fetch current status
    fetchStatusField(
      `/api/conversations/${conversationId}/status/current-status`,
      (data) =>
        setCurrentStatus({
          ...currentStatus,
          value: data.current_status || "",
          isLoading: false,
          error: null,
        }),
      (error) =>
        setCurrentStatus({
          ...currentStatus,
          isLoading: false,
          error,
        }),
    );
  }, [conversationId, intent, definitionOfDone, currentStatus, t]);

  const renderStatusField = (field: StatusField) => {
    let content;
    if (field.isLoading) {
      content = (
        <div className="flex items-center justify-center py-2">
          <LoadingSpinner size="small" />
        </div>
      );
    } else if (field.error) {
      content = <div className="text-red-400 text-sm">{field.error}</div>;
    } else {
      content = <div className="text-sm text-neutral-200">{field.value}</div>;
    }

    return (
      <div className="mb-6">
        <h3 className="text-sm font-medium text-neutral-300 mb-2">
          {field.title}
        </h3>
        <div className="bg-base-primary p-3 rounded-md border border-neutral-700">
          {content}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full w-full overflow-auto p-4 bg-base-secondary">
      <div className="max-w-3xl mx-auto">
        {renderStatusField(intent)}
        {renderStatusField(definitionOfDone)}
        {renderStatusField(currentStatus)}
      </div>
    </div>
  );
}
