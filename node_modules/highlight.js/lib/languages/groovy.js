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
 Language: Groovy
 Author: Guillaume Laforge <glaforge@gmail.com>
 Description: Groovy programming language implementation inspired from Vsevolod's Java mode
 Website: https://groovy-lang.org
 */

function variants(variants, obj = {}) {
  obj.variants = variants;
  return obj;
}

function groovy(hljs) {
  const IDENT_RE = '[A-Za-z0-9_$]+';
  const COMMENT = variants([
    hljs.C_LINE_COMMENT_MODE,
    hljs.C_BLOCK_COMMENT_MODE,
    hljs.COMMENT(
      '/\\*\\*',
      '\\*/',
      {
        relevance: 0,
        contains: [
          {
            // eat up @'s in emails to prevent them to be recognized as doctags
            begin: /\w+@/,
            relevance: 0
          },
          {
            className: 'doctag',
            begin: '@[A-Za-z]+'
          }
        ]
      }
    )
  ]);
  const REGEXP = {
    className: 'regexp',
    begin: /~?\/[^\/\n]+\//,
    contains: [ hljs.BACKSLASH_ESCAPE ]
  };
  const NUMBER = variants([
    hljs.BINARY_NUMBER_MODE,
    hljs.C_NUMBER_MODE
  ]);
  const STRING = variants([
    {
      begin: /"""/,
      end: /"""/
    },
    {
      begin: /'''/,
      end: /'''/
    },
    {
      begin: "\\$/",
      end: "/\\$",
      relevance: 10
    },
    hljs.APOS_STRING_MODE,
    hljs.QUOTE_STRING_MODE
  ],
  {
    className: "string"
  }
  );

  return {
    name: 'Groovy',
    keywords: {
      built_in: 'this super',
      literal: 'true false null',
      keyword:
            'byte short char int long boolean float double void ' +
            // groovy specific keywords
            'def as in assert trait ' +
            // common keywords with Java
            'abstract static volatile transient public private protected synchronized final ' +
            'class interface enum if else for while switch case break default continue ' +
            'throw throws try catch finally implements extends new import package return instanceof'
    },
    contains: [
      hljs.SHEBANG({
        binary: "groovy",
        relevance: 10
      }),
      COMMENT,
      STRING,
      REGEXP,
      NUMBER,
      {
        className: 'class',
        beginKeywords: 'class interface trait enum',
        end: /\{/,
        illegal: ':',
        contains: [
          {
            beginKeywords: 'extends implements'
          },
          hljs.UNDERSCORE_TITLE_MODE
        ]
      },
      {
        className: 'meta',
        begin: '@[A-Za-z]+',
        relevance: 0
      },
      {
        // highlight map keys and named parameters as attrs
        className: 'attr',
        begin: IDENT_RE + '[ \t]*:',
        relevance: 0
      },
      {
        // catch middle element of the ternary operator
        // to avoid highlight it as a label, named parameter, or map key
        begin: /\?/,
        end: /:/,
        relevance: 0,
        contains: [
          COMMENT,
          STRING,
          REGEXP,
          NUMBER,
          'self'
        ]
      },
      {
        // highlight labeled statements
        className: 'symbol',
        begin: '^[ \t]*' + lookahead(IDENT_RE + ':'),
        excludeBegin: true,
        end: IDENT_RE + ':',
        relevance: 0
      }
    ],
    illegal: /#|<\//
  };
}

module.exports = groovy;
