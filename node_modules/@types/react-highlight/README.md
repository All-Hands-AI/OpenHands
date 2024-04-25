# Installation
> `npm install --save @types/react-highlight`

# Summary
This package contains type definitions for react-highlight (https://github.com/akiran/react-highlight).

# Details
Files were exported from https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/react-highlight.
## [index.d.ts](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/react-highlight/index.d.ts)
````ts
import * as React from "react";

/**
 * Props for a Highlight component.
 */
export interface HighlightProps {
    children?: React.ReactNode;
    /**
     * Language name to use as a class to signal type to highlight.js.
     */
    className?: string | undefined;
    /**
     * Set innerHTML=true to highlight multiple code snippets at a time.
     */
    innerHTML?: boolean | undefined;
}

/**
 * Visually prettifies child code with highlight.js.
 */
declare const Highlight: React.ComponentClass<HighlightProps>;

export default Highlight;

````

### Additional Details
 * Last updated: Tue, 07 Nov 2023 09:09:39 GMT
 * Dependencies: [@types/react](https://npmjs.com/package/@types/react)

# Credits
These definitions were written by [JP Lew](https://github.com/jplew).
