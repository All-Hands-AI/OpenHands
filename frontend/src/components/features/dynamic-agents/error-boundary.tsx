
import React from 'react';
import { ErrorToast } from '~/components/shared/error-toast';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class DynamicAgentErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    hasError: false,
    error: null
  };
  
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error
    };
  }
  
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Dynamic Agent Error:', error, info);
  }
  
  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-white rounded-lg shadow">
          <h3 className="text-lg font-medium text-red-600 mb-2">
            Something went wrong
          </h3>
          <ErrorToast 
            error={this.state.error!}
            onRetry={this.handleRetry}
          />
        </div>
      );
    }
    
    return this.props.children;
  }
}

export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>
): React.FC<P> {
  return function WrappedComponent(props: P) {
    return (
      <DynamicAgentErrorBoundary>
        <Component {...props} />
      </DynamicAgentErrorBoundary>
    );
  };
}

export const AgentListWithErrorBoundary = withErrorBoundary(AgentList);
