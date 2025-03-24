import { useNavigate } from "react-router";
import { useCallback } from "react";
import OpenHands from "#/api/open-hands";
import { BrandButton } from "#/components/features/settings/brand-button";

export default function TOSPage() {
  const navigate = useNavigate();

  const handleAcceptTOS = useCallback(async () => {
    try {
      const success = await OpenHands.acceptTOS();
      if (success) {
        // Get the last page from localStorage or default to root
        const lastPage = localStorage.getItem("openhands_last_page") || "/";
        navigate(lastPage);
      }
    } catch (error) {
      console.error("Failed to accept TOS:", error);
    }
  }, [navigate]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>

        <div className="prose dark:prose-invert mb-8">
          <p>
            Welcome to OpenHands. To continue using our service, you must read
            and accept our Terms of Service.
          </p>

          <div className="my-6">
            <p className="mb-4">
              Please review our complete Terms of Service at:
            </p>
            <a
              href="https://www.all-hands.dev/tos"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 underline"
            >
              https://www.all-hands.dev/tos
            </a>
          </div>

          <p className="mt-6">
            By clicking &quot;Accept Terms of Service&quot; below, you
            acknowledge that you have read, understood, and agree to be bound by
            the Terms of Service.
          </p>
        </div>

        <div className="flex justify-center">
          <BrandButton
            variant="primary"
            type="button"
            onClick={handleAcceptTOS}
          >
            Accept Terms of Service
          </BrandButton>
        </div>
      </div>
    </div>
  );
}
