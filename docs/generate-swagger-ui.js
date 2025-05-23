const fs = require('fs');
const path = require('path');
const swaggerUiDist = require('swagger-ui-dist');

/**
 * This script manually sets up Swagger UI for the Docusaurus documentation.
 *
 * Why we need this approach:
 * 1. Docusaurus doesn't have a built-in way to integrate Swagger UI
 * 2. We need to copy the necessary files from swagger-ui-dist to our static directory
 * 3. We need to create a custom index.html file that points to our OpenAPI spec
 * 4. This approach allows us to customize the Swagger UI to match our documentation style
 */

// Get the absolute path to the swagger-ui-dist package
const swaggerUiDistPath = swaggerUiDist.getAbsoluteFSPath();

// Create the target directory if it doesn't exist
const targetDir = path.join(__dirname, 'static', 'swagger-ui');
if (!fs.existsSync(targetDir)) {
  fs.mkdirSync(targetDir, { recursive: true });
}

// Copy all files from swagger-ui-dist to our target directory
const files = fs.readdirSync(swaggerUiDistPath);
files.forEach(file => {
  const sourcePath = path.join(swaggerUiDistPath, file);
  const targetPath = path.join(targetDir, file);

  // Skip directories and non-essential files
  if (fs.statSync(sourcePath).isDirectory() ||
      file === 'package.json' ||
      file === 'README.md' ||
      file.endsWith('.map')) {
    return;
  }

  fs.copyFileSync(sourcePath, targetPath);
});

// Create a custom index.html file that points to our OpenAPI spec
const indexHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OpenHands API Documentation</title>
  <link rel="stylesheet" type="text/css" href="./swagger-ui.css" />
  <link rel="icon" type="image/png" href="./favicon-32x32.png" sizes="32x32" />
  <link rel="icon" type="image/png" href="./favicon-16x16.png" sizes="16x16" />
  <style>
    html {
      box-sizing: border-box;
      overflow: -moz-scrollbars-vertical;
      overflow-y: scroll;
    }

    *,
    *:before,
    *:after {
      box-sizing: inherit;
    }

    body {
      margin: 0;
      background: #fafafa;
    }
  </style>
</head>

<body>
  <div id="swagger-ui"></div>

  <script src="./swagger-ui-bundle.js" charset="UTF-8"> </script>
  <script src="./swagger-ui-standalone-preset.js" charset="UTF-8"> </script>
  <script>
    window.onload = function() {
      // Begin Swagger UI call region
      const ui = SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout"
      });
      // End Swagger UI call region
      window.ui = ui;
    };
  </script>
</body>
</html>
`;

fs.writeFileSync(path.join(targetDir, 'index.html'), indexHtml);

console.log('Swagger UI files generated successfully in static/swagger-ui/');
