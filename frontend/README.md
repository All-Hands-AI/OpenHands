# Getting Started with the OpenDevin Frontend

## Available Scripts

In the project directory, you can run:

### `npm run start -- --port 3001`

Runs the app in the development mode.\
Open [http://localhost:3001](http://localhost:3001) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm run make-i18n`

This command is used to generate the i18n declaration file.\
It should be run when first setting up the repository or when updating translations.

### `npm run test`

This command runs the available test suites for the application.\
It launches the test runner in the interactive watch mode, allowing you to see the results of your tests in real time.

### `npm run build`

Builds the app for production to the `dist` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

## Environment Variables
You can set the environment variables in `frontend/.env` to configure the frontend. The following variables are available:
```javascript
VITE_BACKEND_HOST="127.0.0.1:3000" // The host of the backend
VITE_USE_TLS="false"               // Whether to use TLS for the backend(includes HTTPS and WSS)
VITE_INSECURE_SKIP_VERIFY="false"  // Whether to skip verifying the backend's certificate. Only takes effect if `VITE_USE_TLS` is true. Don't use this in production!
VITE_FRONTEND_PORT="3001"          // The port of the frontend
```
You can also set the environment variables from outside the project, like `exporter VITE_BACKEND_HOST="127.0.0.1:3000"`.

The outside environment variables will override the ones in the `.env` file.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

For more information on tests, you can refer to the official documentation of [Vitest](https://vitest.dev/) and [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/).
