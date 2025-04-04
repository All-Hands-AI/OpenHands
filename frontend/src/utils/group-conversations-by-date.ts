import { Conversation } from "#/api/open-hands.types";

type GroupedConversations = {
  today: Conversation[];
  yesterday: Conversation[];
  thisWeek: Conversation[];
  thisMonth: Conversation[];
  older: Conversation[];
};

export const groupConversationsByDate = (
  conversations: Conversation[],
): GroupedConversations => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const thisWeekStart = new Date(today);
  thisWeekStart.setDate(thisWeekStart.getDate() - thisWeekStart.getDay());
  const thisMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);

  return conversations.reduce<GroupedConversations>(
    (groups, conversation) => {
      const createdAt = new Date(conversation.created_at);
      const createdDate = new Date(
        createdAt.getFullYear(),
        createdAt.getMonth(),
        createdAt.getDate(),
      );

      if (createdDate.getTime() === today.getTime()) {
        groups.today.push(conversation);
      } else if (createdDate.getTime() === yesterday.getTime()) {
        groups.yesterday.push(conversation);
      } else if (createdDate >= thisWeekStart) {
        groups.thisWeek.push(conversation);
      } else if (createdDate >= thisMonthStart) {
        groups.thisMonth.push(conversation);
      } else {
        groups.older.push(conversation);
      }

      return groups;
    },
    {
      today: [],
      yesterday: [],
      thisWeek: [],
      thisMonth: [],
      older: [],
    },
  );
};
