# Getting Started with the OpenDevin Frontend

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm run build`

Builds the app for production to the `dist` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

## Terminal

The OpenDevin terminal is powered by [Xterm.js](https://github.com/xtermjs/xterm.js).

The terminal listens for events over a WebSocket connection. The WebSocket URL is specified by the environment variable `REACT_APP_TERMINAL_WS_URL` (prepending `REACT_APP_` to environment variable names is necessary to expose them).

A simple websocket server can be found in the `/server` directory.
