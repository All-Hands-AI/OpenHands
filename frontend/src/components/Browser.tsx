import React from "react";
import { useSelector } from "react-redux";
import { HiOutlineMagnifyingGlass } from "react-icons/hi2";
import { HiCursorClick } from "react-icons/hi";
import { RootState } from "#/store";

import logo from "../assets/logo.png";

function BlankPage(): JSX.Element {
  return (
    <div className="h-full bg-slate-200 flex flex-col items-center justify-center">
      <img src={logo} alt="Blank Page" className="w-28 h-28" />
      <div className="h-8 flex items-center bg-slate-900 px-2 rounded-3xl ml-3 space-x-2">
        <HiOutlineMagnifyingGlass size={20} />
        <span>OpenDevin: Code Less, Make More.</span>
        <HiCursorClick size={20} />
      </div>
    </div>
  );
}

function Browser(): JSX.Element {
  const { url, screenshotSrc } = useSelector(
    (state: RootState) => state.browser,
  );

  const imgSrc =
    screenshotSrc && screenshotSrc.startsWith("data:image/png;base64,")
      ? screenshotSrc
      : `data:image/png;base64,${screenshotSrc || ""}`;

  return (
    <div className="h-full w-full flex flex-col justify-evenly p-2 space-y-2">
      <div className="w-full py-2 px-5 rounded-3xl bg-neutral-700 text-gray-200 truncate">
        {url}
      </div>
      <div className="overflow-y-auto h-4/5 scrollbar-hide rounded-xl">
        {screenshotSrc ? (
          <img src={imgSrc} className="rounded-xl" alt="Browser Screenshot" />
        ) : (
          <BlankPage />
        )}
      </div>
    </div>
  );
}

export default Browser;
