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

/**
 * Any of the passed expresssions may match
 *
 * Creates a huge this | this | that | that match
 * @param {(RegExp | string)[] } args
 * @returns {string}
 */
function either(...args) {
  const joined = '(' + args.map((x) => source(x)).join("|") + ")";
  return joined;
}

/*
Language: TOML, also INI
Description: TOML aims to be a minimal configuration file format that's easy to read due to obvious semantics.
Contributors: Guillaume Gomez <guillaume1.gomez@gmail.com>
Category: common, config
Website: https://github.com/toml-lang/toml
*/

function ini(hljs) {
  const NUMBERS = {
    className: 'number',
    relevance: 0,
    variants: [
      {
        begin: /([+-]+)?[\d]+_[\d_]+/
      },
      {
        begin: hljs.NUMBER_RE
      }
    ]
  };
  const COMMENTS = hljs.COMMENT();
  COMMENTS.variants = [
    {
      begin: /;/,
      end: /$/
    },
    {
      begin: /#/,
      end: /$/
    }
  ];
  const VARIABLES = {
    className: 'variable',
    variants: [
      {
        begin: /\$[\w\d"][\w\d_]*/
      },
      {
        begin: /\$\{(.*?)\}/
      }
    ]
  };
  const LITERALS = {
    className: 'literal',
    begin: /\bon|off|true|false|yes|no\b/
  };
  const STRINGS = {
    className: "string",
    contains: [hljs.BACKSLASH_ESCAPE],
    variants: [
      {
        begin: "'''",
        end: "'''",
        relevance: 10
      },
      {
        begin: '"""',
        end: '"""',
        relevance: 10
      },
      {
        begin: '"',
        end: '"'
      },
      {
        begin: "'",
        end: "'"
      }
    ]
  };
  const ARRAY = {
    begin: /\[/,
    end: /\]/,
    contains: [
      COMMENTS,
      LITERALS,
      VARIABLES,
      STRINGS,
      NUMBERS,
      'self'
    ],
    relevance: 0
  };

  const BARE_KEY = /[A-Za-z0-9_-]+/;
  const QUOTED_KEY_DOUBLE_QUOTE = /"(\\"|[^"])*"/;
  const QUOTED_KEY_SINGLE_QUOTE = /'[^']*'/;
  const ANY_KEY = either(
    BARE_KEY, QUOTED_KEY_DOUBLE_QUOTE, QUOTED_KEY_SINGLE_QUOTE
  );
  const DOTTED_KEY = concat(
    ANY_KEY, '(\\s*\\.\\s*', ANY_KEY, ')*',
    lookahead(/\s*=\s*[^#\s]/)
  );

  return {
    name: 'TOML, also INI',
    aliases: ['toml'],
    case_insensitive: true,
    illegal: /\S/,
    contains: [
      COMMENTS,
      {
        className: 'section',
        begin: /\[+/,
        end: /\]+/
      },
      {
        begin: DOTTED_KEY,
        className: 'attr',
        starts: {
          end: /$/,
          contains: [
            COMMENTS,
            ARRAY,
            LITERALS,
            VARIABLES,
            STRINGS,
            NUMBERS
          ]
        }
      }
    ]
  };
}

module.exports = ini;
