import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { openHands } from './open-hands-axios';
import { retrieveAxiosErrorMessage } from '../utils/retrieve-axios-error-message';
import { displayErrorToast } from '../utils/custom-toast-handlers';

// Create a custom base query that uses the existing axios instance
const axiosBaseQuery = () => async ({ url, method, data, params }) => {
  try {
    const result = await openHands({
      url,
      method,
      data,
      params,
    });
    return { data: result.data };
  } catch (error) {
    const errorMessage = retrieveAxiosErrorMessage(error);
    displayErrorToast(errorMessage || 'An error occurred');
    return {
      error: {
        status: error.response?.status,
        data: error.response?.data || error.message,
      },
    };
  }
};

// Create the API service
export const apiService = createApi({
  reducerPath: 'api',
  baseQuery: axiosBaseQuery(),
  tagTypes: [
    'Config', 
    'Files', 
    'File', 
    'User', 
    'Conversations', 
    'Conversation',
    'Settings',
    'Balance',
    'VSCodeUrl',
    'Repositories',
    'Installations',
    'Policy',
    'RiskSeverity',
    'Traces',
    'ActiveHost',
  ],
  endpoints: () => ({}),
});