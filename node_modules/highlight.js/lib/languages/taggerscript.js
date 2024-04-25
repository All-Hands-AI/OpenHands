/*
Language: Tagger Script
Author: Philipp Wolfer <ph.wolfer@gmail.com>
Description: Syntax Highlighting for the Tagger Script as used by MusicBrainz Picard.
Website: https://picard.musicbrainz.org
 */
function taggerscript(hljs) {
  const COMMENT = {
    className: 'comment',
    begin: /\$noop\(/,
    end: /\)/,
    contains: [ {
      begin: /\(/,
      end: /\)/,
      contains: [ 'self',
        {
          begin: /\\./
        } ]
    } ],
    relevance: 10
  };

  const FUNCTION = {
    className: 'keyword',
    begin: /\$(?!noop)[a-zA-Z][_a-zA-Z0-9]*/,
    end: /\(/,
    excludeEnd: true
  };

  const VARIABLE = {
    className: 'variable',
    begin: /%[_a-zA-Z0-9:]*/,
    end: '%'
  };

  const ESCAPE_SEQUENCE = {
    className: 'symbol',
    begin: /\\./
  };

  return {
    name: 'Tagger Script',
    contains: [
      COMMENT,
      FUNCTION,
      VARIABLE,
      ESCAPE_SEQUENCE
    ]
  };
}

module.exports = taggerscript;
