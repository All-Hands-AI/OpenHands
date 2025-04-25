import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useUserConversations } from "#/hooks/query/use-user-conversations";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ConversationCard } from "#/components/features/conversation-panel/conversation-card";
import { NavLink } from "react-router";

export default function AgentsPage() {
  const { t } = useTranslation();
  const { data: conversations, isFetching, error } = useUserConversations();

  // Filter only active (RUNNING) conversations
  const activeConversations = conversations?.filter(
    (conversation) => conversation.status === "RUNNING"
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">{t(I18nKey.AGENTS$ACTIVE_AGENTS)}</h1>
      
      {isFetching && (
        <div className="w-full flex justify-center items-center py-12">
          <LoadingSpinner size="medium" />
        </div>
      )}
      
      {error && (
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-danger">{error.message}</p>
        </div>
      )}
      
      {activeConversations?.length === 0 && !isFetching && (
        <div className="flex flex-col items-center justify-center py-12 text-neutral-400">
          <p>{t(I18nKey.AGENTS$NO_ACTIVE_AGENTS)}</p>
        </div>
      )}
      
      <div className="grid grid-cols-1 gap-4">
        {activeConversations?.map((conversation) => (
          <NavLink
            key={conversation.conversation_id}
            to={`/conversations/${conversation.conversation_id}`}
          >
            {({ isActive }) => (
              <ConversationCard
                isActive={isActive}
                title={conversation.title}
                selectedRepository={conversation.selected_repository}
                lastUpdatedAt={conversation.last_updated_at}
                createdAt={conversation.created_at}
                status={conversation.status}
                conversationId={conversation.conversation_id}
                showOptions={true}
              />
            )}
          </NavLink>
        ))}
      </div>
    </div>
  );
}