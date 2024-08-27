import React from "react";
import { json, Link, Outlet, useLoaderData } from "react-router-dom";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { ghClient } from "#/api/github";

type LoaderReturnType = {
  user: GitHubUser;
};

export const loader = async () => {
  const user = await ghClient.getUser();
  return json({ user });
};

function RootLayout() {
  const { user } = useLoaderData() as LoaderReturnType;

  return (
    <div className="bg-root-primary p-3 h-screen flex gap-3">
      <aside className="px-1 flex flex-col gap-[15px]">
        <Link to="/">
          <AllHandsLogo width={34} height={23} />
        </Link>
        <nav className="py-[18px] flex flex-col gap-[18px]">
          <img
            src={user.avatar_url}
            alt={`${user.login} avatar`}
            className="w-8 h-8 rounded-full"
          />
          <div className="w-8 h-8 rounded-full bg-green-100" />
          <div className="w-8 h-8 rounded-full bg-blue-100" />
        </nav>
      </aside>
      <div className="w-full">
        <Outlet />
      </div>
    </div>
  );
}

export default RootLayout;
