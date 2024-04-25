/*
Language: F#
Author: Jonas Follesø <jonas@follesoe.no>
Contributors: Troy Kershaw <hello@troykershaw.com>, Henrik Feldt <henrik@haf.se>
Website: https://docs.microsoft.com/en-us/dotnet/fsharp/
Category: functional
*/

/** @type LanguageFn */
function fsharp(hljs) {
  const TYPEPARAM = {
    begin: '<',
    end: '>',
    contains: [
      hljs.inherit(hljs.TITLE_MODE, {
        begin: /'[a-zA-Z0-9_]+/
      })
    ]
  };

  return {
    name: 'F#',
    aliases: ['fs'],
    keywords:
      'abstract and as assert base begin class default delegate do done ' +
      'downcast downto elif else end exception extern false finally for ' +
      'fun function global if in inherit inline interface internal lazy let ' +
      'match member module mutable namespace new null of open or ' +
      'override private public rec return sig static struct then to ' +
      'true try type upcast use val void when while with yield',
    illegal: /\/\*/,
    contains: [
      {
        // monad builder keywords (matches before non-bang kws)
        className: 'keyword',
        begin: /\b(yield|return|let|do)!/
      },
      {
        className: 'string',
        begin: '@"',
        end: '"',
        contains: [
          {
            begin: '""'
          }
        ]
      },
      {
        className: 'string',
        begin: '"""',
        end: '"""'
      },
      hljs.COMMENT('\\(\\*(\\s)', '\\*\\)', {
        contains: ["self"]
      }),
      {
        className: 'class',
        beginKeywords: 'type',
        end: '\\(|=|$',
        excludeEnd: true,
        contains: [
          hljs.UNDERSCORE_TITLE_MODE,
          TYPEPARAM
        ]
      },
      {
        className: 'meta',
        begin: '\\[<',
        end: '>\\]',
        relevance: 10
      },
      {
        className: 'symbol',
        begin: '\\B(\'[A-Za-z])\\b',
        contains: [hljs.BACKSLASH_ESCAPE]
      },
      hljs.C_LINE_COMMENT_MODE,
      hljs.inherit(hljs.QUOTE_STRING_MODE, {
        illegal: null
      }),
      hljs.C_NUMBER_MODE
    ]
  };
}

module.exports = fsharp;
