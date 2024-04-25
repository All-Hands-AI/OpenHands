/*
Language: Diff
Description: Unified and context diff
Author: Vasily Polovnyov <vast@whiteants.net>
Website: https://www.gnu.org/software/diffutils/
Category: common
*/

/** @type LanguageFn */
function diff(hljs) {
  return {
    name: 'Diff',
    aliases: ['patch'],
    contains: [
      {
        className: 'meta',
        relevance: 10,
        variants: [
          {
            begin: /^@@ +-\d+,\d+ +\+\d+,\d+ +@@/
          },
          {
            begin: /^\*\*\* +\d+,\d+ +\*\*\*\*$/
          },
          {
            begin: /^--- +\d+,\d+ +----$/
          }
        ]
      },
      {
        className: 'comment',
        variants: [
          {
            begin: /Index: /,
            end: /$/
          },
          {
            begin: /^index/,
            end: /$/
          },
          {
            begin: /={3,}/,
            end: /$/
          },
          {
            begin: /^-{3}/,
            end: /$/
          },
          {
            begin: /^\*{3} /,
            end: /$/
          },
          {
            begin: /^\+{3}/,
            end: /$/
          },
          {
            begin: /^\*{15}$/
          },
          {
            begin: /^diff --git/,
            end: /$/
          }
        ]
      },
      {
        className: 'addition',
        begin: /^\+/,
        end: /$/
      },
      {
        className: 'deletion',
        begin: /^-/,
        end: /$/
      },
      {
        className: 'addition',
        begin: /^!/,
        end: /$/
      }
    ]
  };
}

module.exports = diff;
