/*
Language: Elixir
Author: Josh Adams <josh@isotope11.com>
Description: language definition for Elixir source code files (.ex and .exs).  Based on ruby language support.
Category: functional
Website: https://elixir-lang.org
*/

/** @type LanguageFn */
function elixir(hljs) {
  const ELIXIR_IDENT_RE = '[a-zA-Z_][a-zA-Z0-9_.]*(!|\\?)?';
  const ELIXIR_METHOD_RE = '[a-zA-Z_]\\w*[!?=]?|[-+~]@|<<|>>|=~|===?|<=>|[<>]=?|\\*\\*|[-/+%^&*~`|]|\\[\\]=?';
  const ELIXIR_KEYWORDS = {
    $pattern: ELIXIR_IDENT_RE,
    keyword: 'and false then defined module in return redo retry end for true self when ' +
    'next until do begin unless nil break not case cond alias while ensure or ' +
    'include use alias fn quote require import with|0'
  };
  const SUBST = {
    className: 'subst',
    begin: /#\{/,
    end: /\}/,
    keywords: ELIXIR_KEYWORDS
  };
  const NUMBER = {
    className: 'number',
    begin: '(\\b0o[0-7_]+)|(\\b0b[01_]+)|(\\b0x[0-9a-fA-F_]+)|(-?\\b[1-9][0-9_]*(\\.[0-9_]+([eE][-+]?[0-9]+)?)?)',
    relevance: 0
  };
  const SIGIL_DELIMITERS = '[/|([{<"\']';
  const LOWERCASE_SIGIL = {
    className: 'string',
    begin: '~[a-z]' + '(?=' + SIGIL_DELIMITERS + ')',
    contains: [
      {
        endsParent: true,
        contains: [
          {
            contains: [
              hljs.BACKSLASH_ESCAPE,
              SUBST
            ],
            variants: [
              {
                begin: /"/,
                end: /"/
              },
              {
                begin: /'/,
                end: /'/
              },
              {
                begin: /\//,
                end: /\//
              },
              {
                begin: /\|/,
                end: /\|/
              },
              {
                begin: /\(/,
                end: /\)/
              },
              {
                begin: /\[/,
                end: /\]/
              },
              {
                begin: /\{/,
                end: /\}/
              },
              {
                begin: /</,
                end: />/
              }
            ]
          }
        ]
      }
    ]
  };

  const UPCASE_SIGIL = {
    className: 'string',
    begin: '~[A-Z]' + '(?=' + SIGIL_DELIMITERS + ')',
    contains: [
      {
        begin: /"/,
        end: /"/
      },
      {
        begin: /'/,
        end: /'/
      },
      {
        begin: /\//,
        end: /\//
      },
      {
        begin: /\|/,
        end: /\|/
      },
      {
        begin: /\(/,
        end: /\)/
      },
      {
        begin: /\[/,
        end: /\]/
      },
      {
        begin: /\{/,
        end: /\}/
      },
      {
        begin: /</,
        end: />/
      }
    ]
  };

  const STRING = {
    className: 'string',
    contains: [
      hljs.BACKSLASH_ESCAPE,
      SUBST
    ],
    variants: [
      {
        begin: /"""/,
        end: /"""/
      },
      {
        begin: /'''/,
        end: /'''/
      },
      {
        begin: /~S"""/,
        end: /"""/,
        contains: [] // override default
      },
      {
        begin: /~S"/,
        end: /"/,
        contains: [] // override default
      },
      {
        begin: /~S'''/,
        end: /'''/,
        contains: [] // override default
      },
      {
        begin: /~S'/,
        end: /'/,
        contains: [] // override default
      },
      {
        begin: /'/,
        end: /'/
      },
      {
        begin: /"/,
        end: /"/
      }
    ]
  };
  const FUNCTION = {
    className: 'function',
    beginKeywords: 'def defp defmacro',
    end: /\B\b/, // the mode is ended by the title
    contains: [
      hljs.inherit(hljs.TITLE_MODE, {
        begin: ELIXIR_IDENT_RE,
        endsParent: true
      })
    ]
  };
  const CLASS = hljs.inherit(FUNCTION, {
    className: 'class',
    beginKeywords: 'defimpl defmodule defprotocol defrecord',
    end: /\bdo\b|$|;/
  });
  const ELIXIR_DEFAULT_CONTAINS = [
    STRING,
    UPCASE_SIGIL,
    LOWERCASE_SIGIL,
    hljs.HASH_COMMENT_MODE,
    CLASS,
    FUNCTION,
    {
      begin: '::'
    },
    {
      className: 'symbol',
      begin: ':(?![\\s:])',
      contains: [
        STRING,
        {
          begin: ELIXIR_METHOD_RE
        }
      ],
      relevance: 0
    },
    {
      className: 'symbol',
      begin: ELIXIR_IDENT_RE + ':(?!:)',
      relevance: 0
    },
    NUMBER,
    {
      className: 'variable',
      begin: '(\\$\\W)|((\\$|@@?)(\\w+))'
    },
    {
      begin: '->'
    },
    { // regexp container
      begin: '(' + hljs.RE_STARTERS_RE + ')\\s*',
      contains: [
        hljs.HASH_COMMENT_MODE,
        {
          // to prevent false regex triggers for the division function:
          // /:
          begin: /\/: (?=\d+\s*[,\]])/,
          relevance: 0,
          contains: [NUMBER]
        },
        {
          className: 'regexp',
          illegal: '\\n',
          contains: [
            hljs.BACKSLASH_ESCAPE,
            SUBST
          ],
          variants: [
            {
              begin: '/',
              end: '/[a-z]*'
            },
            {
              begin: '%r\\[',
              end: '\\][a-z]*'
            }
          ]
        }
      ],
      relevance: 0
    }
  ];
  SUBST.contains = ELIXIR_DEFAULT_CONTAINS;

  return {
    name: 'Elixir',
    keywords: ELIXIR_KEYWORDS,
    contains: ELIXIR_DEFAULT_CONTAINS
  };
}

module.exports = elixir;
