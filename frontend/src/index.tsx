import * as React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { Provider } from "react-redux";
import { NextUIProvider } from "@nextui-org/react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Main from "./pages/Main";
import reportWebVitals from "./reportWebVitals";
import store from "#/store";
import "#/i18n";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement,
);
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <NextUIProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Main />} />
            {/* Add more routes here */}
          </Routes>
        </Router>
      </NextUIProvider>
    </Provider>
  </React.StrictMode>,
);
//
// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
