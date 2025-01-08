import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import { ConversationPanel } from '~/components/features/conversation-panel/conversation-panel';
import OpenHands from '~/api/open-hands';
import { AuthProvider } from '~/context/auth-context';
import * as EndSession from '~/hooks/use-end-session';

const mockStore = configureStore({
  reducer: {
    chat: (state = {}, action) => state,
  },
});

const mockEndSession = jest.fn();
jest.spyOn(EndSession, 'useEndSession').mockReturnValue(mockEndSession);

const mockConversations = [
  {
    id: '1',
    name: 'Test Conversation 1',
    lastMessage: 'Hello',
    lastActive: '2023-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Test Conversation 2',
    lastMessage: 'World',
    lastActive: '2023-01-02T00:00:00Z',
  },
];

const renderComponent = (props = {}) => {
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
    jest.clearAllMocks();
  });

  it('should render the conversations', async () => {
    jest.spyOn(OpenHands, 'listConversations').mockResolvedValue(mockConversations);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
      expect(screen.getByText('Test Conversation 2')).toBeInTheDocument();
    });
  });

  it('should display an empty state when there are no conversations', async () => {
    jest.spyOn(OpenHands, 'listConversations').mockResolvedValue([]);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('No conversations yet')).toBeInTheDocument();
    });
  });

  it('should handle an error when fetching conversations', async () => {
    jest.spyOn(OpenHands, 'listConversations').mockRejectedValue(new Error('Failed to fetch'));

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Error: Failed to fetch')).toBeInTheDocument();
    });
  });

  it('should cancel deleting a conversation', async () => {
    jest.spyOn(OpenHands, 'listConversations').mockResolvedValue(mockConversations);
    const deleteConversation = jest.spyOn(OpenHands, 'deleteConversation');

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('delete-conversation-1'));
    fireEvent.click(screen.getByText('Cancel'));

    expect(deleteConversation).not.toHaveBeenCalled();
  });

  it('should call endSession after deleting a conversation that is the current session', async () => {
    jest.spyOn(OpenHands, 'listConversations').mockResolvedValue(mockConversations);
    jest.spyOn(OpenHands, 'deleteConversation').mockResolvedValue(undefined);

    renderComponent({ currentSessionId: '1' });

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
    jest.spyOn(OpenHands, 'listConversations').mockResolvedValue(mockConversations);
    const deleteConversation = jest.spyOn(OpenHands, 'deleteConversation').mockResolvedValue(undefined);

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
    jest.spyOn(OpenHands, 'listConversations').mockResolvedValue(mockConversations);
    const updateConversation = jest.spyOn(OpenHands, 'updateConversation').mockResolvedValue({
      ...mockConversations[0],
      name: 'New Name',
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('rename-conversation-1'));
    const input = screen.getByDisplayValue('Test Conversation 1');
    fireEvent.change(input, { target: { value: 'New Name' } });
    fireEvent.click(screen.getByText('Save'));

    await waitFor(() => {
      expect(updateConversation).toHaveBeenCalledWith('1', { name: 'New Name' });
    });
  });

  it('should not rename a conversation when the name is unchanged', async () => {
    jest.spyOn(OpenHands, 'listConversations').mockResolvedValue(mockConversations);
    const updateConversation = jest.spyOn(OpenHands, 'updateConversation');

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('rename-conversation-1'));
    fireEvent.click(screen.getByText('Save'));

    expect(updateConversation).not.toHaveBeenCalled();
  });

  it('should call onClose after clicking a card', async () => {
    jest.spyOn(OpenHands, 'listConversations').mockResolvedValue(mockConversations);
    const onClose = jest.fn();

    renderComponent({ onClose });

    await waitFor(() => {
      expect(screen.getByText('Test Conversation 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Test Conversation 1'));

    expect(onClose).toHaveBeenCalled();
  });
});