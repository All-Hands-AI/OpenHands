import i18n from "i18next";
import Backend from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

export const AvailableLanguages = [
  { label: "English", value: "en" },
  { label: "日本語", value: "ja" },
  { label: "简体中文", value: "zh-CN" },
  { label: "繁體中文", value: "zh-TW" },
  { label: "한국어", value: "ko-KR" },
  { label: "Norsk", value: "no" },
  { label: "Arabic", value: "ar" },
  { label: "Deutsch", value: "de" },
  { label: "Français", value: "fr" },
  { label: "Italiano", value: "it" },
  { label: "Português", value: "pt" },
  { label: "Español", value: "es" },
  { label: "Türkçe", value: "tr" },
  { label: "Українська", value: "uk" },
];

// Function to normalize language codes to supported ones
function normalizeLanguageCode(langCode: string): string {
  const supportedLanguages = AvailableLanguages.map((lang) => lang.value);

  // If the exact language is supported, use it
  if (supportedLanguages.includes(langCode)) {
    return langCode;
  }

  // Try to find a base language match (e.g., 'en' for 'en-US@posix')
  const baseLang = langCode.split('-')[0];
  if (supportedLanguages.includes(baseLang)) {
    return baseLang;
  }

  // For Chinese, try to map variants
  if (baseLang === 'zh') {
    // Default to Simplified Chinese for generic 'zh'
    return 'zh-CN';
  }

  // For Korean, try to map variants
  if (baseLang === 'ko') {
    return 'ko-KR';
  }

  // Fall back to English
  return 'en';
}

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: "en",
    debug: import.meta.env.NODE_ENV === "development",

    // Define supported languages explicitly
    supportedLngs: AvailableLanguages.map((lang) => lang.value),

    // This ensures that if a specific language+region isn't found (e.g., en-US),
    // it will try the base language (e.g., en) before falling back to the fallbackLng
    nonExplicitSupportedLngs: true,
  });

// Override the changeLanguage method to normalize language codes
const originalChangeLanguage = i18n.changeLanguage.bind(i18n);
i18n.changeLanguage = (lng?: string, callback?: any) => {
  if (lng) {
    const normalizedLng = normalizeLanguageCode(lng);
    return originalChangeLanguage(normalizedLng, callback);
  }
  return originalChangeLanguage(lng, callback);
};

export default i18n;
