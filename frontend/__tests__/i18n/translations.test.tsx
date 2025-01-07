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
  describe('Translation Coverage', () => {
    it('should have translations for all supported languages', () => {
      // Get all language codes from AvailableLanguages
      const languageCodes = AvailableLanguages.map(lang => lang.value);

      // Keep track of missing translations
      const missingTranslations: { key: string; languages: string[] }[] = [];

      // Check each translation key
      Object.entries(translations).forEach(([key, value]: [string, any]) => {
        if (typeof value === 'object') {
          const missingLangs = languageCodes.filter(lang => {
            // Handle special case for language codes with hyphens
            const langKey = lang.includes('-') ? `${lang}` : lang;
            return value[langKey] === undefined;
          });

          if (missingLangs.length > 0) {
            missingTranslations.push({
              key,
              languages: missingLangs
            });
          }
        }
      });

      // If there are missing translations, create a helpful error message
      if (missingTranslations.length > 0) {
        const errorMessage = `Found missing translations:\n${missingTranslations
          .map(({ key, languages }) => `  - "${key}" is missing translations for: ${languages.join(', ')}`)
          .join('\n')}`;
        throw new Error(errorMessage);
      }

      // Expect no missing translations
      expect(missingTranslations).toHaveLength(0);
    });
  });
});
