export type FontWeight = 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900;

export const fontWeights: Record<FontWeight, string> = {
  "100": "font-thin",
  "200": "font-extralight",
  "300": "font-light",
  "400": "font-normal",
  "500": "font-medium",
  "600": "font-semibold",
  "700": "font-bold",
  "800": "font-extrabold",
  "900": "font-black",
};

export type FontSize = "xxs" | "xs" | "s" | "m" | "l" | "xl" | "xxl" | "xxxl";

export const fontSizes: Record<FontSize, string> = {
  xxs: "tg-xxs",
  xs: "tg-xs",
  s: "tg-s",
  m: "tg-m",
  l: "text-lg",
  xl: "tg-xl",
  xxl: "tg-xxl",
  xxxl: "tg-xxxl",
};
