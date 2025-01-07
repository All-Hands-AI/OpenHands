import i18n from "i18next";
import Backend from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import translations from "./translation.json";

type TranslationValue = {
  en: string;
  ja?: string;
  "zh-CN"?: string;
  "zh-TW"?: string;
  "ko-KR"?: string;
  no?: string;
  ar?: string;
  de?: string;
  fr?: string;
  it?: string;
  pt?: string;
  es?: string;
  tr?: string;
};

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
      en: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).en,
          ]),
        ),
      },
      ja: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).ja || (value as TranslationValue).en,
          ]),
        ),
      },
      "zh-CN": {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue)["zh-CN"] ||
              (value as TranslationValue).en,
          ]),
        ),
      },
      "zh-TW": {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue)["zh-TW"] ||
              (value as TranslationValue).en,
          ]),
        ),
      },
      "ko-KR": {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue)["ko-KR"] ||
              (value as TranslationValue).en,
          ]),
        ),
      },
      no: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).no || (value as TranslationValue).en,
          ]),
        ),
      },
      ar: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).ar || (value as TranslationValue).en,
          ]),
        ),
      },
      de: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).de || (value as TranslationValue).en,
          ]),
        ),
      },
      fr: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).fr || (value as TranslationValue).en,
          ]),
        ),
      },
      it: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).it || (value as TranslationValue).en,
          ]),
        ),
      },
      pt: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).pt || (value as TranslationValue).en,
          ]),
        ),
      },
      es: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).es || (value as TranslationValue).en,
          ]),
        ),
      },
      tr: {
        translation: Object.fromEntries(
          Object.entries(translations).map(([key, value]) => [
            key,
            (value as TranslationValue).tr || (value as TranslationValue).en,
          ]),
        ),
      },
    },
  });

export default i18n;
