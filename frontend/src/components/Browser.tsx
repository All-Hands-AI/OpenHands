import React from "react";
import "./Browser.css";
import { useSelector } from "react-redux";
import { RootState } from "../store";

// type UrlBarProps = {
//   url: string;
// };

// function UrlBar({ url }: UrlBarProps): JSX.Element {
//   return (
//     <div className="mac-url-bar">
//       <div className="left-icons">
//         <div className="icon icon-red" />
//         <div className="icon icon-yellow" />
//         <div className="icon icon-green" />
//       </div>
//       <div className="url">{url}</div>
//     </div>
//   );
// }

// type ScreenshotProps = {
//   src: string;
// };

// function Screenshot({ src }: ScreenshotProps): JSX.Element {
//   return <img className="screenshot" src={src} alt="screenshot" />;
// }

function Browser(): JSX.Element {
  const url = useSelector((state: RootState) => state.browser.url);
  // const screenshotSrc = useSelector(
  //   (state: RootState) => state.browser.screenshotSrc,
  // );

  return (
    // <div className="browser">
    //   <UrlBar url={url} />
    //   <Screenshot src={screenshotSrc} />
    // </div>
    <div
      className="mockup-browser"
      style={{
        background: "black",
        padding: "1rem",
        height: "90%",
        margin: "1rem",
        borderRadius: "1rem",
      }}
    >
      <div className="mockup-browser-toolbar">
        <div className="input">{url}</div>
      </div>
      {/* <div className="flex justify-center px-4 py-16 bg-base-100 " >Hello World!</div> */}
    </div>
  );
}

export default Browser;
