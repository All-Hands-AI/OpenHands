import React from "react";
import { Link } from "react-router-dom";
import BuildIt from "#/assets/build-it.svg?react";

export function HeroHeading() {
  return (
    <div className="w-[304px] text-center flex flex-col gap-4 items-center py-4">
      <BuildIt width={88} height={104} />
      <h1 className="text-[38px] leading-[32px] -tracking-[0.02em]">
        Let&apos;s Start Building!
      </h1>
      <p className="mx-4 text-sm">
        All Hands makes it easy to build and maintain software using a simple
        prompt. Not sure how to start?{" "}
        <Link
          rel="noopener noreferrer"
          target="_blank"
          to="https://docs.all-hands.dev/modules/usage/agents"
          className="text-hyperlink underline underline-offset-[3px]"
        >
          Read this
        </Link>
      </p>
    </div>
  );
}
