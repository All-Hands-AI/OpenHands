import { chatSlice, addAssistantObservation } from '../src/state/chat-slice';
import { OpenHandsObservation } from '../src/types/core/observations';

describe('chatSlice', () => {
  it('should handle successful read operations', () => {
    const initialState = {
      messages: [
        {
          type: 'action',
          sender: 'assistant',
          eventID: 'test-event-id',
          content: 'Reading file: test.txt',
          imageUrls: [],
          timestamp: new Date().toISOString(),
        },
      ],
    };

    const readObservation: OpenHandsObservation = {
      id: 'test-observation-id',
      observation: 'read',
      cause: 'test-event-id',
      content: 'File content',
      extras: {},
    };

    const action = addAssistantObservation(readObservation);
    const newState = chatSlice.reducer(initialState, action);

    expect(newState.messages[0].success).toBe(true);
  });

  it('should handle successful read operations with empty content', () => {
    const initialState = {
      messages: [
        {
          type: 'action',
          sender: 'assistant',
          eventID: 'test-event-id',
          content: 'Reading file: empty.txt',
          imageUrls: [],
          timestamp: new Date().toISOString(),
        },
      ],
    };

    const readObservation: OpenHandsObservation = {
      id: 'test-observation-id',
      observation: 'read',
      cause: 'test-event-id',
      content: '',
      extras: {},
    };

    const action = addAssistantObservation(readObservation);
    const newState = chatSlice.reducer(initialState, action);

    expect(newState.messages[0].success).toBe(true);
  });

  it('should handle failed read operations', () => {
    const initialState = {
      messages: [
        {
          type: 'action',
          sender: 'assistant',
          eventID: 'test-event-id',
          content: 'Reading file: nonexistent.txt',
          imageUrls: [],
          timestamp: new Date().toISOString(),
        },
      ],
    };

    const readObservation: OpenHandsObservation = {
      id: 'test-observation-id',
      observation: 'read',
      cause: 'test-event-id',
      content: 'ERROR:\nFile not found',
      extras: {},
    };

    const action = addAssistantObservation(readObservation);
    const newState = chatSlice.reducer(initialState, action);

    expect(newState.messages[0].success).toBe(false);
  });

  it('should handle read operations with non-error content containing "error"', () => {
    const initialState = {
      messages: [
        {
          type: 'action',
          sender: 'assistant',
          eventID: 'test-event-id',
          content: 'Reading file: error_description.txt',
          imageUrls: [],
          timestamp: new Date().toISOString(),
        },
      ],
    };

    const readObservation: OpenHandsObservation = {
      id: 'test-observation-id',
      observation: 'read',
      cause: 'test-event-id',
      content: 'This file contains a description of an error, but is not itself an error.',
      extras: {},
    };

    const action = addAssistantObservation(readObservation);
    const newState = chatSlice.reducer(initialState, action);

    expect(newState.messages[0].success).toBe(true);
  });
});