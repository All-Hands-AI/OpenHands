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
 * @param {...(RegExp | string) } args
 * @returns {string}
 */
function concat(...args) {
  const joined = args.map((x) => source(x)).join("");
  return joined;
}

/*
Language: ActionScript
Author: Alexander Myadzel <myadzel@gmail.com>
Category: scripting
Audit: 2020
*/

/** @type LanguageFn */
function actionscript(hljs) {
  const IDENT_RE = /[a-zA-Z_$][a-zA-Z0-9_$]*/;
  const IDENT_FUNC_RETURN_TYPE_RE = /([*]|[a-zA-Z_$][a-zA-Z0-9_$]*)/;

  const AS3_REST_ARG_MODE = {
    className: 'rest_arg',
    begin: /[.]{3}/,
    end: IDENT_RE,
    relevance: 10
  };

  return {
    name: 'ActionScript',
    aliases: [ 'as' ],
    keywords: {
      keyword: 'as break case catch class const continue default delete do dynamic each ' +
        'else extends final finally for function get if implements import in include ' +
        'instanceof interface internal is namespace native new override package private ' +
        'protected public return set static super switch this throw try typeof use var void ' +
        'while with',
      literal: 'true false null undefined'
    },
    contains: [
      hljs.APOS_STRING_MODE,
      hljs.QUOTE_STRING_MODE,
      hljs.C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE,
      hljs.C_NUMBER_MODE,
      {
        className: 'class',
        beginKeywords: 'package',
        end: /\{/,
        contains: [ hljs.TITLE_MODE ]
      },
      {
        className: 'class',
        beginKeywords: 'class interface',
        end: /\{/,
        excludeEnd: true,
        contains: [
          { beginKeywords: 'extends implements' },
          hljs.TITLE_MODE
        ]
      },
      {
        className: 'meta',
        beginKeywords: 'import include',
        end: /;/,
        keywords: { 'meta-keyword': 'import include' }
      },
      {
        className: 'function',
        beginKeywords: 'function',
        end: /[{;]/,
        excludeEnd: true,
        illegal: /\S/,
        contains: [
          hljs.TITLE_MODE,
          {
            className: 'params',
            begin: /\(/,
            end: /\)/,
            contains: [
              hljs.APOS_STRING_MODE,
              hljs.QUOTE_STRING_MODE,
              hljs.C_LINE_COMMENT_MODE,
              hljs.C_BLOCK_COMMENT_MODE,
              AS3_REST_ARG_MODE
            ]
          },
          { begin: concat(/:\s*/, IDENT_FUNC_RETURN_TYPE_RE) }
        ]
      },
      hljs.METHOD_GUARD
    ],
    illegal: /#/
  };
}

module.exports = actionscript;
