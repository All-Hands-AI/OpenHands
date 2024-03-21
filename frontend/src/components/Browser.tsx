import React from "react";
import "./Browser.css";

type UrlBarProps = {
  url: string;
};

function UrlBar({ url }: UrlBarProps): JSX.Element {
  return <div className="url">{url}</div>;
}

type BrowserProps = {
  url: string;
};

function Browser({ url }: BrowserProps): JSX.Element {
  return (
    <div className="browser">
      <UrlBar url={url} />
      <iframe
        className="browser-content"
        src="https://en.wikipedia.org/wiki/Main_Page"
        title="Browser"
      />
    </div>
  );
}

export default Browser;
