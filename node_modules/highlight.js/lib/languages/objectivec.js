/*
Language: Objective-C
Author: Valerii Hiora <valerii.hiora@gmail.com>
Contributors: Angel G. Olloqui <angelgarcia.mail@gmail.com>, Matt Diephouse <matt@diephouse.com>, Andrew Farmer <ahfarmer@gmail.com>, Minh Nguyễn <mxn@1ec5.org>
Website: https://developer.apple.com/documentation/objectivec
Category: common
*/

function objectivec(hljs) {
  const API_CLASS = {
    className: 'built_in',
    begin: '\\b(AV|CA|CF|CG|CI|CL|CM|CN|CT|MK|MP|MTK|MTL|NS|SCN|SK|UI|WK|XC)\\w+'
  };
  const IDENTIFIER_RE = /[a-zA-Z@][a-zA-Z0-9_]*/;
  const OBJC_KEYWORDS = {
    $pattern: IDENTIFIER_RE,
    keyword:
      'int float while char export sizeof typedef const struct for union ' +
      'unsigned long volatile static bool mutable if do return goto void ' +
      'enum else break extern asm case short default double register explicit ' +
      'signed typename this switch continue wchar_t inline readonly assign ' +
      'readwrite self @synchronized id typeof ' +
      'nonatomic super unichar IBOutlet IBAction strong weak copy ' +
      'in out inout bycopy byref oneway __strong __weak __block __autoreleasing ' +
      '@private @protected @public @try @property @end @throw @catch @finally ' +
      '@autoreleasepool @synthesize @dynamic @selector @optional @required ' +
      '@encode @package @import @defs @compatibility_alias ' +
      '__bridge __bridge_transfer __bridge_retained __bridge_retain ' +
      '__covariant __contravariant __kindof ' +
      '_Nonnull _Nullable _Null_unspecified ' +
      '__FUNCTION__ __PRETTY_FUNCTION__ __attribute__ ' +
      'getter setter retain unsafe_unretained ' +
      'nonnull nullable null_unspecified null_resettable class instancetype ' +
      'NS_DESIGNATED_INITIALIZER NS_UNAVAILABLE NS_REQUIRES_SUPER ' +
      'NS_RETURNS_INNER_POINTER NS_INLINE NS_AVAILABLE NS_DEPRECATED ' +
      'NS_ENUM NS_OPTIONS NS_SWIFT_UNAVAILABLE ' +
      'NS_ASSUME_NONNULL_BEGIN NS_ASSUME_NONNULL_END ' +
      'NS_REFINED_FOR_SWIFT NS_SWIFT_NAME NS_SWIFT_NOTHROW ' +
      'NS_DURING NS_HANDLER NS_ENDHANDLER NS_VALUERETURN NS_VOIDRETURN',
    literal:
      'false true FALSE TRUE nil YES NO NULL',
    built_in:
      'BOOL dispatch_once_t dispatch_queue_t dispatch_sync dispatch_async dispatch_once'
  };
  const CLASS_KEYWORDS = {
    $pattern: IDENTIFIER_RE,
    keyword: '@interface @class @protocol @implementation'
  };
  return {
    name: 'Objective-C',
    aliases: [
      'mm',
      'objc',
      'obj-c',
      'obj-c++',
      'objective-c++'
    ],
    keywords: OBJC_KEYWORDS,
    illegal: '</',
    contains: [
      API_CLASS,
      hljs.C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE,
      hljs.C_NUMBER_MODE,
      hljs.QUOTE_STRING_MODE,
      hljs.APOS_STRING_MODE,
      {
        className: 'string',
        variants: [
          {
            begin: '@"',
            end: '"',
            illegal: '\\n',
            contains: [ hljs.BACKSLASH_ESCAPE ]
          }
        ]
      },
      {
        className: 'meta',
        begin: /#\s*[a-z]+\b/,
        end: /$/,
        keywords: {
          'meta-keyword':
            'if else elif endif define undef warning error line ' +
            'pragma ifdef ifndef include'
        },
        contains: [
          {
            begin: /\\\n/,
            relevance: 0
          },
          hljs.inherit(hljs.QUOTE_STRING_MODE, {
            className: 'meta-string'
          }),
          {
            className: 'meta-string',
            begin: /<.*?>/,
            end: /$/,
            illegal: '\\n'
          },
          hljs.C_LINE_COMMENT_MODE,
          hljs.C_BLOCK_COMMENT_MODE
        ]
      },
      {
        className: 'class',
        begin: '(' + CLASS_KEYWORDS.keyword.split(' ').join('|') + ')\\b',
        end: /(\{|$)/,
        excludeEnd: true,
        keywords: CLASS_KEYWORDS,
        contains: [ hljs.UNDERSCORE_TITLE_MODE ]
      },
      {
        begin: '\\.' + hljs.UNDERSCORE_IDENT_RE,
        relevance: 0
      }
    ]
  };
}

module.exports = objectivec;
