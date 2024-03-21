import React from "react";
import "./Browser.css";
import { useSelector } from "react-redux";
import { RootState } from "../store";

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

function Browser(): JSX.Element {
  const url = useSelector((state: RootState) => state.browser.url);
  const screenshotSrc = useSelector(
    (state: RootState) => state.browser.screenshotSrc,
  );

  return (
    <div className="browser">
      <UrlBar url={url} />
      <Screenshot src={screenshotSrc} />
    </div>
  );
}

export default Browser;
