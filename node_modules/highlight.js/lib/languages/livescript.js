const KEYWORDS = [
  "as", // for exports
  "in",
  "of",
  "if",
  "for",
  "while",
  "finally",
  "var",
  "new",
  "function",
  "do",
  "return",
  "void",
  "else",
  "break",
  "catch",
  "instanceof",
  "with",
  "throw",
  "case",
  "default",
  "try",
  "switch",
  "continue",
  "typeof",
  "delete",
  "let",
  "yield",
  "const",
  "class",
  // JS handles these with a special rule
  // "get",
  // "set",
  "debugger",
  "async",
  "await",
  "static",
  "import",
  "from",
  "export",
  "extends"
];
const LITERALS = [
  "true",
  "false",
  "null",
  "undefined",
  "NaN",
  "Infinity"
];

const TYPES = [
  "Intl",
  "DataView",
  "Number",
  "Math",
  "Date",
  "String",
  "RegExp",
  "Object",
  "Function",
  "Boolean",
  "Error",
  "Symbol",
  "Set",
  "Map",
  "WeakSet",
  "WeakMap",
  "Proxy",
  "Reflect",
  "JSON",
  "Promise",
  "Float64Array",
  "Int16Array",
  "Int32Array",
  "Int8Array",
  "Uint16Array",
  "Uint32Array",
  "Float32Array",
  "Array",
  "Uint8Array",
  "Uint8ClampedArray",
  "ArrayBuffer",
  "BigInt64Array",
  "BigUint64Array",
  "BigInt"
];

const ERROR_TYPES = [
  "EvalError",
  "InternalError",
  "RangeError",
  "ReferenceError",
  "SyntaxError",
  "TypeError",
  "URIError"
];

const BUILT_IN_GLOBALS = [
  "setInterval",
  "setTimeout",
  "clearInterval",
  "clearTimeout",

  "require",
  "exports",

  "eval",
  "isFinite",
  "isNaN",
  "parseFloat",
  "parseInt",
  "decodeURI",
  "decodeURIComponent",
  "encodeURI",
  "encodeURIComponent",
  "escape",
  "unescape"
];

const BUILT_IN_VARIABLES = [
  "arguments",
  "this",
  "super",
  "console",
  "window",
  "document",
  "localStorage",
  "module",
  "global" // Node.js
];

const BUILT_INS = [].concat(
  BUILT_IN_GLOBALS,
  BUILT_IN_VARIABLES,
  TYPES,
  ERROR_TYPES
);

/*
Language: LiveScript
Author: Taneli Vatanen <taneli.vatanen@gmail.com>
Contributors: Jen Evers-Corvina <jen@sevvie.net>
Origin: coffeescript.js
Description: LiveScript is a programming language that transcompiles to JavaScript. For info about language see http://livescript.net/
Website: https://livescript.net
Category: scripting
*/

function livescript(hljs) {
  const LIVESCRIPT_BUILT_INS = [
    'npm',
    'print'
  ];
  const LIVESCRIPT_LITERALS = [
    'yes',
    'no',
    'on',
    'off',
    'it',
    'that',
    'void'
  ];
  const LIVESCRIPT_KEYWORDS = [
    'then',
    'unless',
    'until',
    'loop',
    'of',
    'by',
    'when',
    'and',
    'or',
    'is',
    'isnt',
    'not',
    'it',
    'that',
    'otherwise',
    'from',
    'to',
    'til',
    'fallthrough',
    'case',
    'enum',
    'native',
    'list',
    'map',
    '__hasProp',
    '__extends',
    '__slice',
    '__bind',
    '__indexOf'
  ];
  const KEYWORDS$1 = {
    keyword: KEYWORDS.concat(LIVESCRIPT_KEYWORDS),
    literal: LITERALS.concat(LIVESCRIPT_LITERALS),
    built_in: BUILT_INS.concat(LIVESCRIPT_BUILT_INS)
  };
  const JS_IDENT_RE = '[A-Za-z$_](?:-[0-9A-Za-z$_]|[0-9A-Za-z$_])*';
  const TITLE = hljs.inherit(hljs.TITLE_MODE, {
    begin: JS_IDENT_RE
  });
  const SUBST = {
    className: 'subst',
    begin: /#\{/,
    end: /\}/,
    keywords: KEYWORDS$1
  };
  const SUBST_SIMPLE = {
    className: 'subst',
    begin: /#[A-Za-z$_]/,
    end: /(?:-[0-9A-Za-z$_]|[0-9A-Za-z$_])*/,
    keywords: KEYWORDS$1
  };
  const EXPRESSIONS = [
    hljs.BINARY_NUMBER_MODE,
    {
      className: 'number',
      begin: '(\\b0[xX][a-fA-F0-9_]+)|(\\b\\d(\\d|_\\d)*(\\.(\\d(\\d|_\\d)*)?)?(_*[eE]([-+]\\d(_\\d|\\d)*)?)?[_a-z]*)',
      relevance: 0,
      starts: {
        end: '(\\s*/)?',
        relevance: 0
      } // a number tries to eat the following slash to prevent treating it as a regexp
    },
    {
      className: 'string',
      variants: [
        {
          begin: /'''/,
          end: /'''/,
          contains: [hljs.BACKSLASH_ESCAPE]
        },
        {
          begin: /'/,
          end: /'/,
          contains: [hljs.BACKSLASH_ESCAPE]
        },
        {
          begin: /"""/,
          end: /"""/,
          contains: [
            hljs.BACKSLASH_ESCAPE,
            SUBST,
            SUBST_SIMPLE
          ]
        },
        {
          begin: /"/,
          end: /"/,
          contains: [
            hljs.BACKSLASH_ESCAPE,
            SUBST,
            SUBST_SIMPLE
          ]
        },
        {
          begin: /\\/,
          end: /(\s|$)/,
          excludeEnd: true
        }
      ]
    },
    {
      className: 'regexp',
      variants: [
        {
          begin: '//',
          end: '//[gim]*',
          contains: [
            SUBST,
            hljs.HASH_COMMENT_MODE
          ]
        },
        {
          // regex can't start with space to parse x / 2 / 3 as two divisions
          // regex can't start with *, and it supports an "illegal" in the main mode
          begin: /\/(?![ *])(\\.|[^\\\n])*?\/[gim]*(?=\W)/
        }
      ]
    },
    {
      begin: '@' + JS_IDENT_RE
    },
    {
      begin: '``',
      end: '``',
      excludeBegin: true,
      excludeEnd: true,
      subLanguage: 'javascript'
    }
  ];
  SUBST.contains = EXPRESSIONS;

  const PARAMS = {
    className: 'params',
    begin: '\\(',
    returnBegin: true,
    /* We need another contained nameless mode to not have every nested
    pair of parens to be called "params" */
    contains: [
      {
        begin: /\(/,
        end: /\)/,
        keywords: KEYWORDS$1,
        contains: ['self'].concat(EXPRESSIONS)
      }
    ]
  };

  const SYMBOLS = {
    begin: '(#=>|=>|\\|>>|-?->|!->)'
  };

  return {
    name: 'LiveScript',
    aliases: ['ls'],
    keywords: KEYWORDS$1,
    illegal: /\/\*/,
    contains: EXPRESSIONS.concat([
      hljs.COMMENT('\\/\\*', '\\*\\/'),
      hljs.HASH_COMMENT_MODE,
      SYMBOLS, // relevance booster
      {
        className: 'function',
        contains: [
          TITLE,
          PARAMS
        ],
        returnBegin: true,
        variants: [
          {
            begin: '(' + JS_IDENT_RE + '\\s*(?:=|:=)\\s*)?(\\(.*\\)\\s*)?\\B->\\*?',
            end: '->\\*?'
          },
          {
            begin: '(' + JS_IDENT_RE + '\\s*(?:=|:=)\\s*)?!?(\\(.*\\)\\s*)?\\B[-~]{1,2}>\\*?',
            end: '[-~]{1,2}>\\*?'
          },
          {
            begin: '(' + JS_IDENT_RE + '\\s*(?:=|:=)\\s*)?(\\(.*\\)\\s*)?\\B!?[-~]{1,2}>\\*?',
            end: '!?[-~]{1,2}>\\*?'
          }
        ]
      },
      {
        className: 'class',
        beginKeywords: 'class',
        end: '$',
        illegal: /[:="\[\]]/,
        contains: [
          {
            beginKeywords: 'extends',
            endsWithParent: true,
            illegal: /[:="\[\]]/,
            contains: [TITLE]
          },
          TITLE
        ]
      },
      {
        begin: JS_IDENT_RE + ':',
        end: ':',
        returnBegin: true,
        returnEnd: true,
        relevance: 0
      }
    ])
  };
}

module.exports = livescript;
