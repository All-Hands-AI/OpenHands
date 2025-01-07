import i18n from "i18next";
import Backend from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import translations from "./translation.json";

export const AvailableLanguages = [
  { label: "English", value: "en" },
  { label: "简体中文", value: "zh-CN" },
  { label: "繁體中文", value: "zh-TW" },
  { label: "한국어", value: "ko-KR" },
  { label: "日本語", value: "ja" },
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
    debug: import.meta.env.NODE_ENV === "development",
    lng:
      typeof window !== "undefined"
        ? localStorage.getItem("LANGUAGE") || "en"
        : "en",
    resources: {
      en: { translation: translations },
      ja: { translation: translations },
      "zh-CN": { translation: translations },
      "zh-TW": { translation: translations },
      "ko-KR": { translation: translations },
      no: { translation: translations },
      ar: { translation: translations },
      de: { translation: translations },
      fr: { translation: translations },
      it: { translation: translations },
      pt: { translation: translations },
      es: { translation: translations },
      tr: { translation: translations },
    },
  });

export default i18n;
