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

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: "en",
    debug: import.meta.env.NODE_ENV === "development",

    // Define supported languages explicitly
    supportedLngs: AvailableLanguages.map(lang => lang.value),

    // Try to use the exact language first, then fall back to the base language
    load: "currentOnly",

    // This ensures that if a specific language+region isn't found (e.g., en-US),
    // it will try the base language (e.g., en) before falling back to the fallbackLng
    nonExplicitSupportedLngs: true,

    // Language detection options
    detection: {
      // Order of detection methods
      order: ['querystring', 'cookie', 'localStorage', 'navigator'],

      // Cache the detected language
      caches: ['localStorage', 'cookie'],

      // Cookie options
      cookieExpirationDate: new Date(Date.now() + 1000 * 60 * 60 * 24 * 365), // 1 year
      cookieDomain: window.location.hostname,
    },
  });

export default i18n;
