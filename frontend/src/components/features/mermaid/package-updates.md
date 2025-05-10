# Package Updates for Mermaid Support

The following dependencies need to be added to the `package.json` file:

```json
{
  "dependencies": {
    "mermaid": "^10.8.0",
    "@mermaid-js/mermaid-react": "^2.1.0"
  }
}
```

To install these dependencies, run:

```bash
npm install mermaid @mermaid-js/mermaid-react
```

After installation, the Mermaid library needs to be initialized in the application. This can be done in a React component or in a utility file:

```typescript
import mermaid from 'mermaid';

// Initialize mermaid with configuration
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose', // Adjust based on security requirements
  fontFamily: 'monospace',
  flowchart: {
    htmlLabels: true,
    curve: 'linear'
  },
  themeVariables: {
    // Theme variables can be customized here to match the application theme
    primaryColor: '#326BF6',
    primaryTextColor: '#fff',
    primaryBorderColor: '#1F4CDF',
    lineColor: '#666',
    secondaryColor: '#F5F5F5',
    tertiaryColor: '#fff'
  }
});
```

This initialization should be done once when the application loads.