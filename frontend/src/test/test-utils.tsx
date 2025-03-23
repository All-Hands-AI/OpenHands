import React, { ReactNode } from 'react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import store from '../store';
import { AuthProvider } from '../context/auth-context';

// Create a test router with a single route
const createTestRouter = () => createMemoryRouter([
  {
    path: '/',
    element: <div>Test Route</div>,
  },
]);

interface TestWrapperProps {
  children: ReactNode;
}

export function TestWrapper({ children }: TestWrapperProps) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <Provider store={store}>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </AuthProvider>
    </Provider>
  );
}

export function RouterTestWrapper({ children }: TestWrapperProps) {
  const router = createTestRouter();
  
  return (
    <TestWrapper>
      <RouterProvider router={router} />
      {children}
    </TestWrapper>
  );
}