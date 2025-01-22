# Setting Up Search for OpenHands Documentation

This documentation site uses [Algolia DocSearch](https://docsearch.algolia.com/) for its search functionality. To enable search on your local development environment or in production, follow these steps:

## 1. Apply for DocSearch Program

1. Go to the [DocSearch Program](https://docsearch.algolia.com/apply) page
2. Fill out the form with the following details:
   - Website URL: https://docs.all-hands.dev
   - Email: Your maintainer email
   - Repository URL: https://github.com/All-Hands-AI/OpenHands

## 2. Configure Algolia Credentials

Once your application is approved, Algolia will provide you with the following credentials:
- Application ID
- Search-Only API Key
- Index Name

Update these values in `docusaurus.config.ts`:

```typescript
algolia: {
  appId: 'YOUR_APP_ID',
  apiKey: 'YOUR_SEARCH_API_KEY',
  indexName: 'openhands',
  // ... other options
}
```

## 3. Crawling Configuration

Algolia will set up a crawler to index your documentation. The crawler configuration will be managed by the Algolia team, but you can request updates to the crawling pattern if needed.

## 4. Local Development

The search functionality will work in your local development environment as long as you have the correct Algolia credentials configured.

## 5. Production Deployment

The search functionality will automatically work in production once you deploy with the correct Algolia credentials.

## Security Note

Never commit the actual Algolia API keys to the repository. Instead:

1. For local development: Use environment variables or a local `.env` file
2. For production: Set the credentials through your deployment platform's environment variables

## Additional Resources

- [Docusaurus Search Documentation](https://docusaurus.io/docs/search)
- [Algolia DocSearch Documentation](https://docsearch.algolia.com/docs/what-is-docsearch)
