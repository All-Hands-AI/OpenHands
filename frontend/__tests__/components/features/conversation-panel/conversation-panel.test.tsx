import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import { ConversationPanel } from '~/components/features/conversation-panel/conversation-panel';
import OpenHands from '~/api/open-hands';
import { AuthProvider } from '~/context/auth-context';
import * as EndSession from '~/hooks/use-end-session';
import type { Conversation } from '~/api/open-hands.types';

const mockStore = configureStore({
  reducer: {
    chat: (state = {}, action) => state,
  },
});

const mockEndSession = vi.fn();
vi.spyOn(EndSession, 'useEndSession').mockReturnValue(mockEndSession);

const mockConversations: Conversation[] = [
  {
    conversation_id: '1',
    title: 'Test Conversation 1',
    selected_repository: null,
    last_updated_at: '2023-01-01T00:00:00Z',
    created_at: '2023-01-01T00:00:00Z',
    status: 'RUNNING',
  },
  {
    conversation_id: '2',
    title: 'Test Conversation 2',
    selected_repository: null,
    last_updated_at: '2023-01-02T00:00:00Z',
    created_at: '2023-01-02T00:00:00Z',
    status: 'STOPPED',
  },
];

interface Props {
  onClose: () => void;
  currentConversationId?: string;
}

const renderComponent = (props: Props = { onClose: () => {} }) => {
  return render(
    <Provider store={mockStore}>
      <MemoryRouter>
        <AuthProvider>
          <ConversationPanel {...props} />
        </AuthProvider>
      </MemoryRouter>
    </Provider>
  );
};

describe('ConversationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the conversations', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockResolvedValue(mockConversations);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
      expect(screen.getByText('Test Conversation 2')).toBeInTheDocument();
    });
  });

  it('should display an empty state when there are no conversations', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockResolvedValue([]);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('No conversations found')).toBeInTheDocument();
    });
  });

  it('should handle an error when fetching conversations', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockRejectedValue(new Error('Failed to fetch'));

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch')).toBeInTheDocument();
    });
  });

  it('should cancel deleting a conversation', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockResolvedValue(mockConversations);
    const deleteConversation = vi.spyOn(OpenHands, 'deleteUserConversation');

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('delete-conversation-1'));
    fireEvent.click(screen.getByText('Cancel'));

    expect(deleteConversation).not.toHaveBeenCalled();
  });

  it('should call endSession after deleting a conversation that is the current session', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockResolvedValue(mockConversations);
    vi.spyOn(OpenHands, 'deleteUserConversation').mockResolvedValue();

    renderComponent({ onClose: () => {}, currentConversationId: '1' });

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('delete-conversation-1'));
    fireEvent.click(screen.getByText('Delete'));

    await waitFor(() => {
      expect(mockEndSession).toHaveBeenCalled();
    });
  });

  it('should delete a conversation', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockResolvedValue(mockConversations);
    const deleteConversation = vi.spyOn(OpenHands, 'deleteUserConversation').mockResolvedValue();

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('delete-conversation-1'));
    fireEvent.click(screen.getByText('Delete'));

    await waitFor(() => {
      expect(deleteConversation).toHaveBeenCalledWith('1');
    });
  });

  it('should rename a conversation', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockResolvedValue(mockConversations);
    const updateConversation = vi.spyOn(OpenHands, 'updateUserConversation').mockResolvedValue();

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('rename-conversation-1'));
    const input = screen.getByDisplayValue('Test Conversation 1');
    fireEvent.change(input, { target: { value: 'New Name' } });
    fireEvent.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(updateConversation).toHaveBeenCalledWith('1', { title: 'New Name' });
    });
  });

  it('should not rename a conversation when the name is unchanged', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockResolvedValue(mockConversations);
    const updateConversation = vi.spyOn(OpenHands, 'updateUserConversation');

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('rename-conversation-1'));
    fireEvent.click(screen.getByText('Save'));

    expect(updateConversation).not.toHaveBeenCalled();
  });

  it('should call onClose after clicking a card', async () => {
    vi.spyOn(OpenHands, 'getUserConversations').mockResolvedValue(mockConversations);
    const onClose = vi.fn();

    renderComponent({ onClose });

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Test Conversation 1'));

    expect(onClose).toHaveBeenCalled();
  });
});