# OpenDevin Frontend Documentation

Welcome to the documentation for the OpenDevin Frontend project. This guide will help you get started with setting up the project, running it locally, running tests, building for production, and customizing the project configuration.

## Getting Started

To get started with the OpenDevin Frontend, follow these steps:

### 1. Clone the Repository

Clone the repository to your local machine using Git:

```bash
git clone https://github.com/OpenDevin/OpenDevin.git
```

### 2. Install Dependencies

Navigate to the project directory and install dependencies using npm:

```bash
cd opendevin-frontend
npm install
```

### 3. Start the Development Server

Once the dependencies are installed, you can start the development server by running:

```bash
npm start
```

This command will run the app in development mode and open it in your default web browser at [http://localhost:3000](http://localhost:3000).

### 4. Explore the Project

Now that the development server is running, you can explore the project, make changes, and see the results in real-time. The page will automatically reload whenever you make edits.

## Available Scripts

In the project directory, you can use the following npm scripts:

### `npm start`

Runs the app in the development mode.
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.
The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in interactive watch mode.
See the [running tests](https://facebook.github.io/create-react-app/docs/running-tests) section for more information.

### `npm run build`

Builds the app for production to the `build` folder.
It correctly bundles React in production mode and optimizes the build for the best performance.
The build is minified and the filenames include the hashes.
Your app is ready to be deployed!
See the [deployment](https://facebook.github.io/create-react-app/docs/deployment) section for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you eject, you can’t go back!**

If you aren’t satisfied with the build tool and configuration choices, you can eject at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc.) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point, you’re on your own.

You don’t have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn’t feel obligated to use this feature. However, we understand that this tool wouldn’t be useful if you couldn’t customize it when you are ready for it.

## Setting up the Terminal

The OpenDevin terminal is powered by [Xterm.js](https://github.com/xtermjs/xterm.js).

The terminal listens for events over a WebSocket connection. The WebSocket URL is specified by the environment variable `REACT_APP_TERMINAL_WS_URL` (prepending `REACT_APP_` to environment variable names is necessary to expose them).

A simple WebSocket server can be found in the `/server` directory.

## Learn More

You can learn more about Create React App in the [official documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

That's it! You should now be ready to start working with the OpenDevin Frontend project. If you encounter any issues or have questions, feel free to refer to the documentation or reach out to the project maintainers. Happy coding!


