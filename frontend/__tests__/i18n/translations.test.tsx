import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { I18nextProvider } from 'react-i18next';
import i18n from '../../src/i18n';
import { AccountSettingsContextMenu } from '../../src/components/features/context-menu/account-settings-context-menu';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const renderWithI18n = (component: React.ReactNode, language: string = 'en') => {
  i18n.changeLanguage(language);
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>
        {component}
      </I18nextProvider>
    </QueryClientProvider>
  );
};

describe('Translations', () => {
  describe('Account Settings Menu', () => {
    it('should display menu items in English by default', () => {
      renderWithI18n(
        <AccountSettingsContextMenu
          onClickAccountSettings={() => {}}
          onLogout={() => {}}
          onClose={() => {}}
          isLoggedIn={true}
        />
      );
      
      expect(screen.getByText('ACCOUNT_SETTINGS$SETTINGS')).toBeInTheDocument();
      expect(screen.getByText('ACCOUNT_SETTINGS$LOGOUT')).toBeInTheDocument();
    });

    it('should display menu items in Japanese when language is set to ja', () => {
      renderWithI18n(
        <AccountSettingsContextMenu
          onClickAccountSettings={() => {}}
          onLogout={() => {}}
          onClose={() => {}}
          isLoggedIn={true}
        />,
        'ja'
      );
      
      expect(screen.getByText('ACCOUNT_SETTINGS$SETTINGS')).toBeInTheDocument();
      expect(screen.getByText('ACCOUNT_SETTINGS$LOGOUT')).toBeInTheDocument();
    });
  });

  describe('Chat Interface', () => {
    it('should display chat placeholder in English by default', () => {
      renderWithI18n(<div data-testid="chat-input" data-i18n="SUGGESTIONS$WHAT_TO_BUILD">SUGGESTIONS$WHAT_TO_BUILD</div>);
      
      expect(screen.getByText('SUGGESTIONS$WHAT_TO_BUILD')).toBeInTheDocument();
    });

    it('should display chat placeholder in Japanese when language is set to ja', () => {
      renderWithI18n(<div data-testid="chat-input" data-i18n="SUGGESTIONS$WHAT_TO_BUILD">SUGGESTIONS$WHAT_TO_BUILD</div>, 'ja');
      
      expect(screen.getByText('SUGGESTIONS$WHAT_TO_BUILD')).toBeInTheDocument();
    });
  });
});