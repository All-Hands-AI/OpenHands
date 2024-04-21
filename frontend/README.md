# Getting Started with the OpenDevin Frontend

## Available Scripts

In the project directory, you can run:

### `npm run start -- --port 3001`

Runs the app in the development mode.\
Open [http://localhost:3001](http://localhost:3001) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

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
