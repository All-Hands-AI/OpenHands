import { Link } from "@remix-run/react";
import Clipboard from "#/assets/clipboard.svg?react";

function Waitlist() {
  return (
    <div className="bg-neutral-800 h-full flex items-center justify-center rounded-xl">
      <div className="w-[384px] flex flex-col gap-6 bg-neutral-900 rounded-xl p-6">
        <Clipboard className="w-14 self-center" />

        <div className="flex flex-col gap-2">
          <h1 className="text-[20px] leading-6 -tracking-[0.01em] font-semibold">
            You&apos;re not in the waitlist yet!
          </h1>
          <p className="text-neutral-400 text-xs">
            Please click{" "}
            <a
              href="https://www.all-hands.dev/join-waitlist"
              target="_blank"
              rel="noreferrer noopener"
              className="text-blue-500"
            >
              here
            </a>{" "}
            to join the waitlist.
          </p>
        </div>

        <Link
          to="/"
          className="text-white text-sm py-[10px] bg-neutral-500 rounded text-center"
        >
          Go back to home
        </Link>
      </div>
    </div>
  );
}

export default Waitlist;
