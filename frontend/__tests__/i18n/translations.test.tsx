import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { I18nextProvider } from 'react-i18next';
import i18n, { AvailableLanguages } from '../../src/i18n';
import { AccountSettingsContextMenu } from '../../src/components/features/context-menu/account-settings-context-menu';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import translations from '../../src/i18n/translation.json';

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
  it('should render translated text', () => {
    renderWithI18n(<AccountSettingsContextMenu />);
    expect(screen.getByTestId('account-settings-context-menu')).toBeInTheDocument();
  });
});
