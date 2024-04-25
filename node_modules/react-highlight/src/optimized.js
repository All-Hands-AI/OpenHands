import hljs from'highlight.js/lib/highlight';
import React from'react';

class Highlight extends React.Component {
    componentDidMount() {
        this.highlightCode();
    }

    componentDidUpdate() {
        this.highlightCode();
    }

    highlightCode() {
        const {className, languages} = this.props;
        const nodes = this.el.querySelectorAll('pre code');

        if ((languages.length === 0) && className) {
            languages.push(className);
        }

        languages.forEach(lang => {
            hljs.registerLanguage(lang, require('highlight.js/lib/languages/' + lang));
        });

        for (let i = 0; i < nodes.length; i++) {
            hljs.highlightBlock(nodes[i])
        }
    }

    setEl = (el) => {
        this.el = el;
    };

    render() {
        const {children, className, element: Element, innerHTML} = this.props;
        const props = { ref: this.setEl, className };

        if (innerHTML) {
            props.dangerouslySetInnerHTML = { __html: children };
            if (Element) {
                return <Element {...props} />;
            }
            return <div {...props} />;
        }

        if (Element) {
            return <Element {...props}>{children}</Element>;
        }
        return <pre ref={this.setEl}><code className={className}>{children}</code></pre>;
    }
}

Highlight.defaultProps = {
    innerHTML: false,
    className: '',
    languages: [],
};

export default Highlight;
