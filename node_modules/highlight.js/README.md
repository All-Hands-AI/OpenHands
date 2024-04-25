# Highlight.js

[![latest version](https://badgen.net/npm/v/highlight.js?label=latest)](https://www.npmjs.com/package/highlight.js)
[![slack](https://badgen.net/badge/icon/slack?icon=slack&label&color=pink)](https://join.slack.com/t/highlightjs/shared_invite/zt-mj0utgqp-TNFf4VQICnDnPg4zMHChFw)
[![discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=pink)](https://discord.gg/M24EbU7ja9)
[![license](https://badgen.net/github/license/highlightjs/highlight.js?color=cyan)](https://github.com/highlightjs/highlight.js/blob/main/LICENSE)
[![install size](https://badgen.net/packagephobia/install/highlight.js?label=npm+install)](https://packagephobia.now.sh/result?p=highlight.js)
![minified](https://img.shields.io/github/size/highlightjs/cdn-release/build/highlight.min.js?label=minified)
[![NPM downloads weekly](https://badgen.net/npm/dw/highlight.js?label=npm+downloads&color=purple)](https://www.npmjs.com/package/highlight.js)
[![jsDelivr CDN downloads](https://badgen.net/jsdelivr/hits/gh/highlightjs/cdn-release?label=jsDelivr+CDN&color=purple)](https://www.jsdelivr.com/package/gh/highlightjs/cdn-release)
![dev deps](https://badgen.net/david/dev/highlightjs/highlight.js?label=dev+deps)
[![code quality](https://badgen.net/lgtm/grade/g/highlightjs/highlight.js/js)](https://lgtm.com/projects/g/highlightjs/highlight.js/?mode=list)

[![build and CI status](https://badgen.net/github/checks/highlightjs/highlight.js?label=build)](https://github.com/highlightjs/highlight.js/actions?query=workflow%3A%22Node.js+CI%22)
[![open issues](https://badgen.net/github/open-issues/highlightjs/highlight.js?label=issues)](https://github.com/highlightjs/highlight.js/issues)
[![help welcome issues](https://badgen.net/github/label-issues/highlightjs/highlight.js/help%20welcome/open)](https://github.com/highlightjs/highlight.js/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+welcome%22)
[![good first issue](https://badgen.net/github/label-issues/highlightjs/highlight.js/good%20first%20issue/open)](https://github.com/highlightjs/highlight.js/issues?q=is%3Aopen+is%3Aissue+label%3A%22beginner+friendly%22)
[![vulnerabilities](https://badgen.net/snyk/highlightjs/highlight.js)](https://snyk.io/test/github/highlightjs/highlight.js?targetFile=package.json)

<!-- [![Build CI](https://img.shields.io/github/workflow/status/highlightjs/highlight.js/Node.js%20CI)](https://github.com/highlightjs/highlight.js/actions?query=workflow%3A%22Node.js+CI%22) -->
<!-- [![commits since release](https://img.shields.io/github/commits-since/highlightjs/highlight.js/latest?label=commits+since)](https://github.com/highlightjs/highlight.js/commits/main) -->
<!-- [![](https://data.jsdelivr.com/v1/package/gh/highlightjs/cdn-release/badge?style=rounded)](https://www.jsdelivr.com/package/gh/highlightjs/cdn-release) -->
<!-- [![Total Lines](https://img.shields.io/tokei/lines/github/highlightjs/highlight.js)]() -->
<!-- [![npm bundle size (minified + gzip)](https://img.shields.io/bundlephobia/minzip/highlight.js.svg)](https://bundlephobia.com/result?p=highlight.js) -->


Highlight.js is a syntax highlighter written in JavaScript. It works in
the browser as well as on the server. It works with pretty much any
markup, doesn’t depend on any framework, and has automatic language
detection.

#### Upgrading to Version 10

Version 10 is one of the biggest releases in quite some time.  If you're
upgrading from version 9, there are some breaking changes and things you may
want to double check first.

Please read [VERSION_10_UPGRADE.md](https://github.com/highlightjs/highlight.js/blob/main/VERSION_10_UPGRADE.md) for  high-level summary of breaking changes and any actions you may need to take. See [VERSION_10_BREAKING_CHANGES.md](https://github.com/highlightjs/highlight.js/blob/main/VERSION_10_BREAKING_CHANGES.md) for a more detailed list and [CHANGES.md](https://github.com/highlightjs/highlight.js/blob/main/CHANGES.md) to learn what else is new.

##### Support for older versions

Please see [SECURITY.md](https://github.com/highlightjs/highlight.js/blob/main/SECURITY.md) for support information.

## Getting Started

The bare minimum for using highlight.js on a web page is linking to the
library along with one of the styles and calling [`highlightAll`][1]:

```html
<link rel="stylesheet" href="/path/to/styles/default.css">
<script src="/path/to/highlight.min.js"></script>
<script>hljs.highlightAll();</script>
```

This will find and highlight code inside of `<pre><code>` tags; it tries
to detect the language automatically. If automatic detection doesn’t
work for you, you can specify the language in the `class` attribute:

```html
<pre><code class="html">...</code></pre>
```

Classes may also be prefixed with either `language-` or `lang-`.

```html
<pre><code class="language-html">...</code></pre>
```

### Plaintext and Disabling Highlighting

To style arbitrary text like code, but without any highlighting, use the
`plaintext` class:

```html
<pre><code class="plaintext">...</code></pre>
```

To disable highlighting of a tag completely, use the `nohighlight` class:

```html
<pre><code class="nohighlight">...</code></pre>
```

### Supported Languages

Highlight.js supports over 180 different languages in the core library.  There are also 3rd party
language plugins available for additional languages. You can find the full list of supported languages
in [SUPPORTED_LANGUAGES.md][9].

## Custom Scenarios

When you need a bit more control over the initialization of
highlight.js, you can use the [`highlightBlock`][3] and [`configure`][4]
functions. This allows you to better control *what* to highlight and *when*.

Here’s the equivalent of calling [`highlightAll`][1] using
only vanilla JS:

```js
document.addEventListener('DOMContentLoaded', (event) => {
  document.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightBlock(block);
  });
});
```

Please refer to the documentation for [`configure`][4] options.


### Using custom HTML elements for code blocks

We strongly recommend `<pre><code>` wrapping for code blocks. It's quite
semantic and "just works" out of the box with zero fiddling. It is possible to
use other HTML elements (or combos), but you may need to pay special attention to
preserving linebreaks.

Let's say your markup for code blocks uses divs:

```html
<div class='code'>...</div>
```

To highlight such blocks manually:

```js
// first, find all the div.code blocks
document.querySelectorAll('div.code').forEach(block => {
  // then highlight each
  hljs.highlightBlock(block);
});
```

Without using a tag that preserves linebreaks (like `pre`) you'll need some
additional CSS to help preserve them.  You could also [pre and post-process line
breaks with a plug-in][brPlugin], but *we recommend using CSS*.

[brPlugin]: https://github.com/highlightjs/highlight.js/issues/2559

To preserve linebreaks inside a `div` using CSS:

```css
div.code {
  white-space: pre;
}
```


## Using with Vue.js

Simply register the plugin with Vue:

```js
Vue.use(hljs.vuePlugin);
```

And you'll be provided with a `highlightjs` component for use
in your templates:

```html
  <div id="app">
    <!-- bind to a data property named `code` -->
    <highlightjs autodetect :code="code" />
    <!-- or literal code works as well -->
    <highlightjs language='javascript' code="var x = 5;" />
  </div>
```

## Web Workers

You can run highlighting inside a web worker to avoid freezing the browser
window while dealing with very big chunks of code.

In your main script:

```js
addEventListener('load', () => {
  const code = document.querySelector('#code');
  const worker = new Worker('worker.js');
  worker.onmessage = (event) => { code.innerHTML = event.data; }
  worker.postMessage(code.textContent);
});
```

In worker.js:

```js
onmessage = (event) => {
  importScripts('<path>/highlight.min.js');
  const result = self.hljs.highlightAuto(event.data);
  postMessage(result.value);
};
```

## Node.js

You can use highlight.js with node to highlight content before sending it to the browser.
Make sure to use the `.value` property to get the formatted html.
For more info about the returned object refer to the [api docs](https://highlightjs.readthedocs.io/en/latest/api.html).


```js
// require the highlight.js library, including all languages
const hljs = require('./highlight.js');
const highlightedCode = hljs.highlightAuto('<span>Hello World!</span>').value
```

Or for a smaller footprint... load just the languages you need.

```js
const hljs = require('highlight.js/lib/core');  // require only the core library
// separately require languages
hljs.registerLanguage('xml', require('highlight.js/lib/languages/xml'));

const highlightedCode = hljs.highlight('<span>Hello World!</span>', {language: 'xml'}).value
```


## ES6 Modules

First, you'll likely install via `npm` or `yarn` -- see [Getting the Library](#getting-the-library) below.

In your application:

```js
import hljs from 'highlight.js';
```

The default import imports all languages. Therefore it is likely to be more efficient to import only the library and the languages you need:

```js
import hljs from 'highlight.js/lib/core';
import javascript from 'highlight.js/lib/languages/javascript';
hljs.registerLanguage('javascript', javascript);
```

To set the syntax highlighting style, if your build tool processes CSS from your JavaScript entry point, you can also import the stylesheet directly as modules:

```js
import hljs from 'highlight.js/lib/core';
import 'highlight.js/styles/github.css';
```


## Getting the Library

You can get highlight.js as a hosted, or custom-build, browser script or
as a server module. Right out of the box the browser script supports
both AMD and CommonJS, so if you wish you can use RequireJS or
Browserify without having to build from source. The server module also
works perfectly fine with Browserify, but there is the option to use a
build specific to browsers rather than something meant for a server.


**Do not link to GitHub directly.** The library is not supposed to work straight
from the source, it requires building. If none of the pre-packaged options
work for you refer to the [building documentation][6].

**On Almond.** You need to use the optimizer to give the module a name. For
example:

```bash
r.js -o name=hljs paths.hljs=/path/to/highlight out=highlight.js
```

### CDN Hosted

A prebuilt version of Highlight.js bundled with many common languages is hosted by several popular CDNs.
When using Highlight.js via CDN you can use Subresource Integrity for additional security.  For details
see [DIGESTS.md](https://github.com/highlightjs/cdn-release/blob/main/DIGESTS.md).

**cdnjs** ([link](https://cdnjs.com/libraries/highlight.js))

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.7.3/styles/default.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.7.3/highlight.min.js"></script>
<!-- and it's easy to individually load additional languages -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.7.3/languages/go.min.js"></script>
```

**jsdelivr** ([link](https://www.jsdelivr.com/package/gh/highlightjs/cdn-release))

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@10.7.3/build/styles/default.min.css">
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@10.7.3/build/highlight.min.js"></script>
<!-- and it's easy to individually load additional languages -->
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@10.7.3/build/languages/go.min.js"></script>
```

**unpkg** ([link](https://unpkg.com/browse/@highlightjs/cdn-assets/))

```html
<link rel="stylesheet" href="https://unpkg.com/@highlightjs/cdn-assets@10.7.3/styles/default.min.css">
<script src="https://unpkg.com/@highlightjs/cdn-assets@10.7.3/highlight.min.js"></script>
<!-- and it's easy to individually load additional languages -->
<script src="https://unpkg.com/@highlightjs/cdn-assets@10.7.3/languages/go.min.js"></script>
```

**Note:** *The CDN-hosted `highlight.min.js` package doesn't bundle every language.* It would be
very large. You can find our list of "common" languages that we bundle by default on our [download page][5].

### Self Hosting

The [download page][5] can quickly generate a custom bundle including only the languages you need.

Alternatively, you can build a browser package from [source](#source):

```
node tools/build.js -t browser :common
```

See our [building documentation][6] for more information.

**Note:** Building from source should always result in the smallest size builds.  The website download page is optimized for speed, not size.


#### Prebuilt CDN assets

You can also download and self-host the same assets we serve up via our own CDNs.  We publish those builds to the [cdn-release](https://github.com/highlightjs/cdn-release) GitHub repository.  You can easily pull individual files off the CDN endpoints with `curl`, etc; if say you only needed `highlight.min.js` and a single CSS file.

There is also an npm package [@highlightjs/cdn-assets](https://www.npmjs.com/package/@highlightjs/cdn-assets) if pulling the assets in via `npm` or `yarn` would be easier for your build process.


### NPM / Node.js server module

Highlight.js can also be used on the server. The package with all supported languages can be installed from NPM or Yarn:

```bash
npm install highlight.js
# or
yarn add highlight.js
```

Alternatively, you can build it from [source](#source):

```bash
node tools/build.js -t node
```

See our [building documentation][6] for more information.


### Source

[Current source][10] is always available on GitHub.


## License

Highlight.js is released under the BSD License. See [LICENSE][7] file
for details.


## Links

The official site for the library is at <https://highlightjs.org/>.

Further in-depth documentation for the API and other topics is at
<http://highlightjs.readthedocs.io/>.

A list of the Core Team and contributors can be found in the [CONTRIBUTORS.md][8] file.

[1]: http://highlightjs.readthedocs.io/en/latest/api.html#highlightall
[2]: http://highlightjs.readthedocs.io/en/latest/css-classes-reference.html
[3]: http://highlightjs.readthedocs.io/en/latest/api.html#highlightblock-block
[4]: http://highlightjs.readthedocs.io/en/latest/api.html#configure-options
[5]: https://highlightjs.org/download/
[6]: http://highlightjs.readthedocs.io/en/latest/building-testing.html
[7]: https://github.com/highlightjs/highlight.js/blob/main/LICENSE
[8]: https://github.com/highlightjs/highlight.js/blob/main/CONTRIBUTORS.md
[9]: https://github.com/highlightjs/highlight.js/blob/main/SUPPORTED_LANGUAGES.md
[10]: https://github.com/highlightjs/
