import { json } from "@remix-run/react";

export const clientLoader = () => {
  const mode = import.meta.env.VITE_APP_MODE || "oss";

  if (mode !== "saas") {
    throw json({ message: "Not Found" }, { status: 404 });
  }
};

function TOS() {
  return (
    <div>
      <h1>Terms of Service</h1>
      <p>These are the terms of service.</p>
    </div>
  );
}

export default TOS;
