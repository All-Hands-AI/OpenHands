import ansiHTML from 'ansi-html-community';

// Initialize ansi-html
ansiHTML.setColors({
  reset: ['fff', '000'],
  black: '000',
  red: 'f00',
  green: '0f0',
  yellow: 'ff0',
  blue: '00f',
  magenta: 'f0f',
  cyan: '0ff',
  lightgrey: 'eee',
  darkgrey: '666'
});

export function convertAnsiToHtml(text: string): string {
  return ansiHTML(text);
}