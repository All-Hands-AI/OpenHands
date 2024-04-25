/*
Language: Scala
Category: functional
Author: Jan Berkel <jan.berkel@gmail.com>
Contributors: Erik Osheim <d_m@plastic-idolatry.com>
Website: https://www.scala-lang.org
*/

function scala(hljs) {
  const ANNOTATION = {
    className: 'meta',
    begin: '@[A-Za-z]+'
  };

  // used in strings for escaping/interpolation/substitution
  const SUBST = {
    className: 'subst',
    variants: [
      {
        begin: '\\$[A-Za-z0-9_]+'
      },
      {
        begin: /\$\{/,
        end: /\}/
      }
    ]
  };

  const STRING = {
    className: 'string',
    variants: [
      {
        begin: '"""',
        end: '"""'
      },
      {
        begin: '"',
        end: '"',
        illegal: '\\n',
        contains: [ hljs.BACKSLASH_ESCAPE ]
      },
      {
        begin: '[a-z]+"',
        end: '"',
        illegal: '\\n',
        contains: [
          hljs.BACKSLASH_ESCAPE,
          SUBST
        ]
      },
      {
        className: 'string',
        begin: '[a-z]+"""',
        end: '"""',
        contains: [ SUBST ],
        relevance: 10
      }
    ]

  };

  const SYMBOL = {
    className: 'symbol',
    begin: '\'\\w[\\w\\d_]*(?!\')'
  };

  const TYPE = {
    className: 'type',
    begin: '\\b[A-Z][A-Za-z0-9_]*',
    relevance: 0
  };

  const NAME = {
    className: 'title',
    begin: /[^0-9\n\t "'(),.`{}\[\]:;][^\n\t "'(),.`{}\[\]:;]+|[^0-9\n\t "'(),.`{}\[\]:;=]/,
    relevance: 0
  };

  const CLASS = {
    className: 'class',
    beginKeywords: 'class object trait type',
    end: /[:={\[\n;]/,
    excludeEnd: true,
    contains: [
      hljs.C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE,
      {
        beginKeywords: 'extends with',
        relevance: 10
      },
      {
        begin: /\[/,
        end: /\]/,
        excludeBegin: true,
        excludeEnd: true,
        relevance: 0,
        contains: [ TYPE ]
      },
      {
        className: 'params',
        begin: /\(/,
        end: /\)/,
        excludeBegin: true,
        excludeEnd: true,
        relevance: 0,
        contains: [ TYPE ]
      },
      NAME
    ]
  };

  const METHOD = {
    className: 'function',
    beginKeywords: 'def',
    end: /[:={\[(\n;]/,
    excludeEnd: true,
    contains: [ NAME ]
  };

  return {
    name: 'Scala',
    keywords: {
      literal: 'true false null',
      keyword: 'type yield lazy override def with val var sealed abstract private trait object if forSome for while throw finally protected extends import final return else break new catch super class case package default try this match continue throws implicit'
    },
    contains: [
      hljs.C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE,
      STRING,
      SYMBOL,
      TYPE,
      METHOD,
      CLASS,
      hljs.C_NUMBER_MODE,
      ANNOTATION
    ]
  };
}

module.exports = scala;
