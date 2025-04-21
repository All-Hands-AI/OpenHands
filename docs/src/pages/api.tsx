import React, { useEffect } from 'react';
import Layout from '@theme/Layout';
import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import { useColorMode } from '@docusaurus/theme-common';

export default function ApiDocs(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  const { colorMode } = useColorMode();

  useEffect(() => {
    // Add custom styling for dark mode
    if (colorMode === 'dark') {
      document.documentElement.setAttribute('data-swagger-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-swagger-theme');
    }
  }, [colorMode]);

  return (
    <Layout
      title={`API Reference | ${siteConfig.title}`}
      description="OpenHands API Reference Documentation">
      <div className="container margin-vert--lg">
        <div className="row">
          <div className="col">
            <h1>OpenHands API Reference</h1>
            <p>
              This page provides interactive documentation for the OpenHands API.
              You can explore the available endpoints, request/response schemas, and even try out API calls directly from this page.
            </p>
            <div className="swagger-ui-container">
              <SwaggerUI url="/openapi.json" />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}