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
Language: Erlang REPL
Author: Sergey Ignatov <sergey@ignatov.spb.su>
Website: https://www.erlang.org
Category: functional
*/

/** @type LanguageFn */
function erlangRepl(hljs) {
  return {
    name: 'Erlang REPL',
    keywords: {
      built_in:
        'spawn spawn_link self',
      keyword:
        'after and andalso|10 band begin bnot bor bsl bsr bxor case catch cond div end fun if ' +
        'let not of or orelse|10 query receive rem try when xor'
    },
    contains: [
      {
        className: 'meta',
        begin: '^[0-9]+> ',
        relevance: 10
      },
      hljs.COMMENT('%', '$'),
      {
        className: 'number',
        begin: '\\b(\\d+(_\\d+)*#[a-fA-F0-9]+(_[a-fA-F0-9]+)*|\\d+(_\\d+)*(\\.\\d+(_\\d+)*)?([eE][-+]?\\d+)?)',
        relevance: 0
      },
      hljs.APOS_STRING_MODE,
      hljs.QUOTE_STRING_MODE,
      {
        begin: concat(
          /\?(::)?/,
          /([A-Z]\w*)/, // at least one identifier
          /((::)[A-Z]\w*)*/ // perhaps more
        )
      },
      {
        begin: '->'
      },
      {
        begin: 'ok'
      },
      {
        begin: '!'
      },
      {
        begin: '(\\b[a-z\'][a-zA-Z0-9_\']*:[a-z\'][a-zA-Z0-9_\']*)|(\\b[a-z\'][a-zA-Z0-9_\']*)',
        relevance: 0
      },
      {
        begin: '[A-Z][a-zA-Z0-9_\']*',
        relevance: 0
      }
    ]
  };
}

module.exports = erlangRepl;
