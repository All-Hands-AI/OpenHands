import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router";
import { checkTosAcceptance } from "#/utils/check-tos-acceptance";

interface TOSRedirectProps {
  children: React.ReactNode;
}

/**
 * Component that checks if the user has accepted the TOS and redirects to the TOS page if not
 */
export function TOSRedirect({ children }: TOSRedirectProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(true);
  const [hasAcceptedTos, setHasAcceptedTos] = useState(false);

  useEffect(() => {
    const checkTos = async () => {
      try {
        // Skip the check if we're already on the TOS page or login page
        if (location.pathname === "/accept-tos") {
          setIsLoading(false);
          return;
        }

        const hasAccepted = await checkTosAcceptance();
        setHasAcceptedTos(hasAccepted);
        
        if (!hasAccepted) {
          navigate("/accept-tos");
        }
      } catch (error) {
        console.error("Failed to check TOS acceptance:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkTos();
  }, [navigate, location.pathname]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  // If we're on the TOS page or the user has accepted the TOS, render the children
  if (location.pathname === "/accept-tos" || hasAcceptedTos) {
    return <>{children}</>;
  }

  // This should not happen as we redirect to the TOS page if the user hasn't accepted it
  return null;
}