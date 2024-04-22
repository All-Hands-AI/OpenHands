import i18n from "i18next";
import Backend from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import { ArgConfigType } from "#/types/ConfigType";

export const AvailableLanguages = [
  { label: "English", value: "en" },
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
];

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: "en",
    debug: process.env.NODE_ENV === "development",
  })
  .then(() => {
    // assume all detected languages are available
    const detectLanguage = i18n.language;
    // cannot trust browser language setting
    const settingLanguage = localStorage.getItem(ArgConfigType.LANGUAGE);

    // if setting is not initialized, but detected language is available, use detected language and update language setting
    if (
      !settingLanguage &&
      AvailableLanguages.some((lang) => detectLanguage === lang.value)
    ) {
      localStorage.setItem(ArgConfigType.LANGUAGE, detectLanguage);
      i18n.changeLanguage(detectLanguage);
      return;
    }

    // if setting is not initialized and detected language is not available, use en and update language setting
    if (
      !settingLanguage &&
      !AvailableLanguages.some((lang) => detectLanguage === lang.value)
    ) {
      localStorage.setItem("language", "en");
      i18n.changeLanguage("en");
      return;
    }

    // if setting is initialized and setting language is not available, use en and update language setting
    if (
      settingLanguage &&
      !AvailableLanguages.some((lang) => settingLanguage === lang.value)
    ) {
      localStorage.setItem("language", "en");
      i18n.changeLanguage("en");
      return;
    }

    // if setting is initialized and setting language is available, use setting language
    if (settingLanguage && settingLanguage !== detectLanguage) {
      i18n.changeLanguage(settingLanguage);
    }
  });

export default i18n;
