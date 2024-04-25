const MODES = (hljs) => {
  return {
    IMPORTANT: {
      className: 'meta',
      begin: '!important'
    },
    HEXCOLOR: {
      className: 'number',
      begin: '#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})'
    },
    ATTRIBUTE_SELECTOR_MODE: {
      className: 'selector-attr',
      begin: /\[/,
      end: /\]/,
      illegal: '$',
      contains: [
        hljs.APOS_STRING_MODE,
        hljs.QUOTE_STRING_MODE
      ]
    }
  };
};

const TAGS = [
  'a',
  'abbr',
  'address',
  'article',
  'aside',
  'audio',
  'b',
  'blockquote',
  'body',
  'button',
  'canvas',
  'caption',
  'cite',
  'code',
  'dd',
  'del',
  'details',
  'dfn',
  'div',
  'dl',
  'dt',
  'em',
  'fieldset',
  'figcaption',
  'figure',
  'footer',
  'form',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'header',
  'hgroup',
  'html',
  'i',
  'iframe',
  'img',
  'input',
  'ins',
  'kbd',
  'label',
  'legend',
  'li',
  'main',
  'mark',
  'menu',
  'nav',
  'object',
  'ol',
  'p',
  'q',
  'quote',
  'samp',
  'section',
  'span',
  'strong',
  'summary',
  'sup',
  'table',
  'tbody',
  'td',
  'textarea',
  'tfoot',
  'th',
  'thead',
  'time',
  'tr',
  'ul',
  'var',
  'video'
];

const MEDIA_FEATURES = [
  'any-hover',
  'any-pointer',
  'aspect-ratio',
  'color',
  'color-gamut',
  'color-index',
  'device-aspect-ratio',
  'device-height',
  'device-width',
  'display-mode',
  'forced-colors',
  'grid',
  'height',
  'hover',
  'inverted-colors',
  'monochrome',
  'orientation',
  'overflow-block',
  'overflow-inline',
  'pointer',
  'prefers-color-scheme',
  'prefers-contrast',
  'prefers-reduced-motion',
  'prefers-reduced-transparency',
  'resolution',
  'scan',
  'scripting',
  'update',
  'width',
  // TODO: find a better solution?
  'min-width',
  'max-width',
  'min-height',
  'max-height'
];

// https://developer.mozilla.org/en-US/docs/Web/CSS/Pseudo-classes
const PSEUDO_CLASSES = [
  'active',
  'any-link',
  'blank',
  'checked',
  'current',
  'default',
  'defined',
  'dir', // dir()
  'disabled',
  'drop',
  'empty',
  'enabled',
  'first',
  'first-child',
  'first-of-type',
  'fullscreen',
  'future',
  'focus',
  'focus-visible',
  'focus-within',
  'has', // has()
  'host', // host or host()
  'host-context', // host-context()
  'hover',
  'indeterminate',
  'in-range',
  'invalid',
  'is', // is()
  'lang', // lang()
  'last-child',
  'last-of-type',
  'left',
  'link',
  'local-link',
  'not', // not()
  'nth-child', // nth-child()
  'nth-col', // nth-col()
  'nth-last-child', // nth-last-child()
  'nth-last-col', // nth-last-col()
  'nth-last-of-type', //nth-last-of-type()
  'nth-of-type', //nth-of-type()
  'only-child',
  'only-of-type',
  'optional',
  'out-of-range',
  'past',
  'placeholder-shown',
  'read-only',
  'read-write',
  'required',
  'right',
  'root',
  'scope',
  'target',
  'target-within',
  'user-invalid',
  'valid',
  'visited',
  'where' // where()
];

// https://developer.mozilla.org/en-US/docs/Web/CSS/Pseudo-elements
const PSEUDO_ELEMENTS = [
  'after',
  'backdrop',
  'before',
  'cue',
  'cue-region',
  'first-letter',
  'first-line',
  'grammar-error',
  'marker',
  'part',
  'placeholder',
  'selection',
  'slotted',
  'spelling-error'
];

const ATTRIBUTES = [
  'align-content',
  'align-items',
  'align-self',
  'animation',
  'animation-delay',
  'animation-direction',
  'animation-duration',
  'animation-fill-mode',
  'animation-iteration-count',
  'animation-name',
  'animation-play-state',
  'animation-timing-function',
  'auto',
  'backface-visibility',
  'background',
  'background-attachment',
  'background-clip',
  'background-color',
  'background-image',
  'background-origin',
  'background-position',
  'background-repeat',
  'background-size',
  'border',
  'border-bottom',
  'border-bottom-color',
  'border-bottom-left-radius',
  'border-bottom-right-radius',
  'border-bottom-style',
  'border-bottom-width',
  'border-collapse',
  'border-color',
  'border-image',
  'border-image-outset',
  'border-image-repeat',
  'border-image-slice',
  'border-image-source',
  'border-image-width',
  'border-left',
  'border-left-color',
  'border-left-style',
  'border-left-width',
  'border-radius',
  'border-right',
  'border-right-color',
  'border-right-style',
  'border-right-width',
  'border-spacing',
  'border-style',
  'border-top',
  'border-top-color',
  'border-top-left-radius',
  'border-top-right-radius',
  'border-top-style',
  'border-top-width',
  'border-width',
  'bottom',
  'box-decoration-break',
  'box-shadow',
  'box-sizing',
  'break-after',
  'break-before',
  'break-inside',
  'caption-side',
  'clear',
  'clip',
  'clip-path',
  'color',
  'column-count',
  'column-fill',
  'column-gap',
  'column-rule',
  'column-rule-color',
  'column-rule-style',
  'column-rule-width',
  'column-span',
  'column-width',
  'columns',
  'content',
  'counter-increment',
  'counter-reset',
  'cursor',
  'direction',
  'display',
  'empty-cells',
  'filter',
  'flex',
  'flex-basis',
  'flex-direction',
  'flex-flow',
  'flex-grow',
  'flex-shrink',
  'flex-wrap',
  'float',
  'font',
  'font-display',
  'font-family',
  'font-feature-settings',
  'font-kerning',
  'font-language-override',
  'font-size',
  'font-size-adjust',
  'font-smoothing',
  'font-stretch',
  'font-style',
  'font-variant',
  'font-variant-ligatures',
  'font-variation-settings',
  'font-weight',
  'height',
  'hyphens',
  'icon',
  'image-orientation',
  'image-rendering',
  'image-resolution',
  'ime-mode',
  'inherit',
  'initial',
  'justify-content',
  'left',
  'letter-spacing',
  'line-height',
  'list-style',
  'list-style-image',
  'list-style-position',
  'list-style-type',
  'margin',
  'margin-bottom',
  'margin-left',
  'margin-right',
  'margin-top',
  'marks',
  'mask',
  'max-height',
  'max-width',
  'min-height',
  'min-width',
  'nav-down',
  'nav-index',
  'nav-left',
  'nav-right',
  'nav-up',
  'none',
  'normal',
  'object-fit',
  'object-position',
  'opacity',
  'order',
  'orphans',
  'outline',
  'outline-color',
  'outline-offset',
  'outline-style',
  'outline-width',
  'overflow',
  'overflow-wrap',
  'overflow-x',
  'overflow-y',
  'padding',
  'padding-bottom',
  'padding-left',
  'padding-right',
  'padding-top',
  'page-break-after',
  'page-break-before',
  'page-break-inside',
  'perspective',
  'perspective-origin',
  'pointer-events',
  'position',
  'quotes',
  'resize',
  'right',
  'src', // @font-face
  'tab-size',
  'table-layout',
  'text-align',
  'text-align-last',
  'text-decoration',
  'text-decoration-color',
  'text-decoration-line',
  'text-decoration-style',
  'text-indent',
  'text-overflow',
  'text-rendering',
  'text-shadow',
  'text-transform',
  'text-underline-position',
  'top',
  'transform',
  'transform-origin',
  'transform-style',
  'transition',
  'transition-delay',
  'transition-duration',
  'transition-property',
  'transition-timing-function',
  'unicode-bidi',
  'vertical-align',
  'visibility',
  'white-space',
  'widows',
  'width',
  'word-break',
  'word-spacing',
  'word-wrap',
  'z-index'
  // reverse makes sure longer attributes `font-weight` are matched fully
  // instead of getting false positives on say `font`
].reverse();

/**
 * @param {string} value
 * @returns {RegExp}
 * */

/**
 * @param {RegExp | string } re
 * @returns {string}
 */
function source(re) {
  if (!re) return null;
  if (typeof re === "string") return re;

  return re.source;
}

/**
 * @param {RegExp | string } re
 * @returns {string}
 */
function lookahead(re) {
  return concat('(?=', re, ')');
}

/**
 * @param {...(RegExp | string) } args
 * @returns {string}
 */
function concat(...args) {
  const joined = args.map((x) => source(x)).join("");
  return joined;
}

/*
Language: CSS
Category: common, css
Website: https://developer.mozilla.org/en-US/docs/Web/CSS
*/

/** @type LanguageFn */
function css(hljs) {
  const modes = MODES(hljs);
  const FUNCTION_DISPATCH = {
    className: "built_in",
    begin: /[\w-]+(?=\()/
  };
  const VENDOR_PREFIX = {
    begin: /-(webkit|moz|ms|o)-(?=[a-z])/
  };
  const AT_MODIFIERS = "and or not only";
  const AT_PROPERTY_RE = /@-?\w[\w]*(-\w+)*/; // @-webkit-keyframes
  const IDENT_RE = '[a-zA-Z-][a-zA-Z0-9_-]*';
  const STRINGS = [
    hljs.APOS_STRING_MODE,
    hljs.QUOTE_STRING_MODE
  ];

  return {
    name: 'CSS',
    case_insensitive: true,
    illegal: /[=|'\$]/,
    keywords: {
      keyframePosition: "from to"
    },
    classNameAliases: {
      // for visual continuity with `tag {}` and because we
      // don't have a great class for this?
      keyframePosition: "selector-tag"
    },
    contains: [
      hljs.C_BLOCK_COMMENT_MODE,
      VENDOR_PREFIX,
      // to recognize keyframe 40% etc which are outside the scope of our
      // attribute value mode
      hljs.CSS_NUMBER_MODE,
      {
        className: 'selector-id',
        begin: /#[A-Za-z0-9_-]+/,
        relevance: 0
      },
      {
        className: 'selector-class',
        begin: '\\.' + IDENT_RE,
        relevance: 0
      },
      modes.ATTRIBUTE_SELECTOR_MODE,
      {
        className: 'selector-pseudo',
        variants: [
          {
            begin: ':(' + PSEUDO_CLASSES.join('|') + ')'
          },
          {
            begin: '::(' + PSEUDO_ELEMENTS.join('|') + ')'
          }
        ]
      },
      // we may actually need this (12/2020)
      // { // pseudo-selector params
      //   begin: /\(/,
      //   end: /\)/,
      //   contains: [ hljs.CSS_NUMBER_MODE ]
      // },
      {
        className: 'attribute',
        begin: '\\b(' + ATTRIBUTES.join('|') + ')\\b'
      },
      // attribute values
      {
        begin: ':',
        end: '[;}]',
        contains: [
          modes.HEXCOLOR,
          modes.IMPORTANT,
          hljs.CSS_NUMBER_MODE,
          ...STRINGS,
          // needed to highlight these as strings and to avoid issues with
          // illegal characters that might be inside urls that would tigger the
          // languages illegal stack
          {
            begin: /(url|data-uri)\(/,
            end: /\)/,
            relevance: 0, // from keywords
            keywords: {
              built_in: "url data-uri"
            },
            contains: [
              {
                className: "string",
                // any character other than `)` as in `url()` will be the start
                // of a string, which ends with `)` (from the parent mode)
                begin: /[^)]/,
                endsWithParent: true,
                excludeEnd: true
              }
            ]
          },
          FUNCTION_DISPATCH
        ]
      },
      {
        begin: lookahead(/@/),
        end: '[{;]',
        relevance: 0,
        illegal: /:/, // break on Less variables @var: ...
        contains: [
          {
            className: 'keyword',
            begin: AT_PROPERTY_RE
          },
          {
            begin: /\s/,
            endsWithParent: true,
            excludeEnd: true,
            relevance: 0,
            keywords: {
              $pattern: /[a-z-]+/,
              keyword: AT_MODIFIERS,
              attribute: MEDIA_FEATURES.join(" ")
            },
            contains: [
              {
                begin: /[a-z-]+(?=:)/,
                className: "attribute"
              },
              ...STRINGS,
              hljs.CSS_NUMBER_MODE
            ]
          }
        ]
      },
      {
        className: 'selector-tag',
        begin: '\\b(' + TAGS.join('|') + ')\\b'
      }
    ]
  };
}

module.exports = css;
