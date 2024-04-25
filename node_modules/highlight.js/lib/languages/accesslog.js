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
 Language: Apache Access Log
 Author: Oleg Efimov <efimovov@gmail.com>
 Description: Apache/Nginx Access Logs
 Website: https://httpd.apache.org/docs/2.4/logs.html#accesslog
 Audit: 2020
 */

/** @type LanguageFn */
function accesslog(_hljs) {
  // https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
  const HTTP_VERBS = [
    "GET",
    "POST",
    "HEAD",
    "PUT",
    "DELETE",
    "CONNECT",
    "OPTIONS",
    "PATCH",
    "TRACE"
  ];
  return {
    name: 'Apache Access Log',
    contains: [
      // IP
      {
        className: 'number',
        begin: /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?\b/,
        relevance: 5
      },
      // Other numbers
      {
        className: 'number',
        begin: /\b\d+\b/,
        relevance: 0
      },
      // Requests
      {
        className: 'string',
        begin: concat(/"/, either(...HTTP_VERBS)),
        end: /"/,
        keywords: HTTP_VERBS,
        illegal: /\n/,
        relevance: 5,
        contains: [
          {
            begin: /HTTP\/[12]\.\d'/,
            relevance: 5
          }
        ]
      },
      // Dates
      {
        className: 'string',
        // dates must have a certain length, this prevents matching
        // simple array accesses a[123] and [] and other common patterns
        // found in other languages
        begin: /\[\d[^\]\n]{8,}\]/,
        illegal: /\n/,
        relevance: 1
      },
      {
        className: 'string',
        begin: /\[/,
        end: /\]/,
        illegal: /\n/,
        relevance: 0
      },
      // User agent / relevance boost
      {
        className: 'string',
        begin: /"Mozilla\/\d\.\d \(/,
        end: /"/,
        illegal: /\n/,
        relevance: 3
      },
      // Strings
      {
        className: 'string',
        begin: /"/,
        end: /"/,
        illegal: /\n/,
        relevance: 0
      }
    ]
  };
}

module.exports = accesslog;
