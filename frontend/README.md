# Getting Started with the OpenHands Frontend

## Overview

This is the frontend of the OpenHands project. It is a React application that provides a web interface for the OpenHands project.

## Tech Stack

- Remix SPA Mode (React + Vite + React Router)
- TypeScript
- Redux
- TanStack Query
- Tailwind CSS
- i18next
- React Testing Library
- Vitest
- Mock Service Worker

## Getting Started

### Prerequisites

- Node.js 20.x or later
- `npm`, `bun`, or any other package manager that supports the `package.json` file

### Installation

```sh
# Clone the repository
git clone https://github.com/All-Hands-AI/OpenHands.git

# Change the directory to the frontend
cd OpenHands/frontend

# Install the dependencies
npm install
```

### Running the Application in Development Mode

We use `msw` to mock the backend API. To start the application with the mocked backend, run the following command:

```sh
npm run dev
```

This will start the application in development mode. Open [http://localhost:3001](http://localhost:3001) to view it in the browser.

**NOTE: The backend is _partially_ mocked using `msw`. Therefore, some features may not work as they would with the actual backend.**

### Running the Application with the Actual Backend (Production Mode)

There are two ways to run the application with the actual backend:

```sh
# Build the application from the root directory
make build

# Start the application
make start
```

OR

```sh
# Start the backend from the root directory
make start-backend

# Build the frontend
cd frontend && npm run build

# Serve the frontend
npm start -- --port 3001
```

### Environment Variables

The frontend application uses the following environment variables:

| Variable                    | Description                                                            | Default Value    |
| --------------------------- | ---------------------------------------------------------------------- | ---------------- |
| `VITE_BACKEND_BASE_URL`     | The backend hostname without protocol (used for WebSocket connections) | `localhost:3000` |
| `VITE_BACKEND_HOST`         | The backend host with port for API connections                         | `127.0.0.1:3000` |
| `VITE_MOCK_API`             | Enable/disable API mocking with MSW                                    | `false`          |
| `VITE_MOCK_SAAS`            | Simulate SaaS mode in development                                      | `false`          |
| `VITE_USE_TLS`              | Use HTTPS/WSS for backend connections                                  | `false`          |
| `VITE_FRONTEND_PORT`        | Port to run the frontend application                                   | `3001`           |
| `VITE_INSECURE_SKIP_VERIFY` | Skip TLS certificate verification                                      | `false`          |
| `VITE_GITHUB_TOKEN`         | GitHub token for repository access (used in some tests)                | -                |

You can create a `.env` file in the frontend directory with these variables based on the `.env.sample` file.

### Project Structure

```sh
frontend
├── __tests__ # Tests
├── public
├── src
│   ├── api # API calls
│   ├── assets
│   ├── components
│   ├── context # Local state management
│   ├── hooks # Custom hooks
│   ├── i18n # Internationalization
│   ├── mocks # MSW mocks for development
│   ├── routes # React Router file-based routes
│   ├── services
│   ├── state # Redux state management
│   ├── types
│   ├── utils # Utility/helper functions
│   └── root.tsx # Entry point
└── .env.sample # Sample environment variables
```

#### Components

Components are organized into folders based on their **domain**, **feature**, or **shared functionality**.

```sh
components
├── features # Domain-specific components
├── layout
├── modals
└── ui # Shared UI components
```

### Features

- Real-time updates with WebSockets
- Internationalization
- Router data loading with Remix
- User authentication with GitHub OAuth (if saas mode is enabled)

## Testing

We use `Vitest` for testing. To run the tests, run the following command:

```sh
npm run test
```

## Contributing

Please read the [CONTRIBUTING.md](../CONTRIBUTING.md) file for details on our code of conduct, and the process for submitting pull requests to us.

## Troubleshooting

TODO
