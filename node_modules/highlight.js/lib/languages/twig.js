/*
Language: Twig
Requires: xml.js
Author: Luke Holder <lukemh@gmail.com>
Description: Twig is a templating language for PHP
Website: https://twig.symfony.com
Category: template
*/

function twig(hljs) {
  var PARAMS = {
    className: 'params',
    begin: '\\(', end: '\\)'
  };

  var FUNCTION_NAMES = 'attribute block constant cycle date dump include ' +
                  'max min parent random range source template_from_string';

  var FUNCTIONS = {
    beginKeywords: FUNCTION_NAMES,
    keywords: {name: FUNCTION_NAMES},
    relevance: 0,
    contains: [
      PARAMS
    ]
  };

  var FILTER = {
    begin: /\|[A-Za-z_]+:?/,
    keywords:
      'abs batch capitalize column convert_encoding date date_modify default ' +
      'escape filter first format inky_to_html inline_css join json_encode keys last ' +
      'length lower map markdown merge nl2br number_format raw reduce replace ' +
      'reverse round slice sort spaceless split striptags title trim upper url_encode',
    contains: [
      FUNCTIONS
    ]
  };

  var TAGS = 'apply autoescape block deprecated do embed extends filter flush for from ' +
    'if import include macro sandbox set use verbatim with';

  TAGS = TAGS + ' ' + TAGS.split(' ').map(function(t){return 'end' + t}).join(' ');

  return {
    name: 'Twig',
    aliases: ['craftcms'],
    case_insensitive: true,
    subLanguage: 'xml',
    contains: [
      hljs.COMMENT(/\{#/, /#\}/),
      {
        className: 'template-tag',
        begin: /\{%/, end: /%\}/,
        contains: [
          {
            className: 'name',
            begin: /\w+/,
            keywords: TAGS,
            starts: {
              endsWithParent: true,
              contains: [FILTER, FUNCTIONS],
              relevance: 0
            }
          }
        ]
      },
      {
        className: 'template-variable',
        begin: /\{\{/, end: /\}\}/,
        contains: ['self', FILTER, FUNCTIONS]
      }
    ]
  };
}

module.exports = twig;
