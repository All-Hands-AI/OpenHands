import React from "react";
import "./Browser.css";

type UrlBarProps = {
  url: string;
};

function UrlBar({ url }: UrlBarProps): JSX.Element {
  return <div className="url">{url}</div>;
}

type ScreenshotProps = {
  src: string;
};

function Screenshot({ src }: ScreenshotProps): JSX.Element {
  return <img className="screenshot" src={src} alt="screenshot" />;
}

type BrowserProps = {
  url: string;
  screenshotSrc: string;
};

function Browser({ url, screenshotSrc }: BrowserProps): JSX.Element {
  return (
    <div className="browser">
      <UrlBar url={url} />
      <Screenshot src={screenshotSrc} />
    </div>
  );
}

export default Browser;
