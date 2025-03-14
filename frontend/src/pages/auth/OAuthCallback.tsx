import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router";

export default function OAuthCallback() {
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");

    if (token) {
      // Store token in localStorage
      localStorage.setItem("token", token);

      // Redirect to home page
      window.location.href = "/";
    } else {
      setError("Authentication failed. No token received.");
    }
  }, [searchParams]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-8">
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">{error}</h3>
              </div>
            </div>
          </div>
          <button
            onClick={() => {
              window.location.href = "/login";
            }}
            className="group relative flex w-full justify-center rounded-md bg-indigo-600 py-2 px-3 text-sm font-semibold text-white hover:bg-indigo-500"
            type="button"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            Authenticating...
          </h2>
        </div>
      </div>
    </div>
  );
}
