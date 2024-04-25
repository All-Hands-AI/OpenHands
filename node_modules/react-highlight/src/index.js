import hljs from 'highlight.js';
import React from 'react';

class Highlight extends React.Component {
    constructor(props) {
      super(props)
      this.setEl = this.setEl.bind(this)
    }
    componentDidMount() {
        this.highlightCode();
    }

    componentDidUpdate() {
        this.highlightCode();
    }

    highlightCode() {
        const nodes = this.el.querySelectorAll('pre code');

        for (let i = 0; i < nodes.length; i++) {
            hljs.highlightBlock(nodes[i])
        }
    }

    setEl(el) {
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
    className: null,
    element: null,
};

export default Highlight;
