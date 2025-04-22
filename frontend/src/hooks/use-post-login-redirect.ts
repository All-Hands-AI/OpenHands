import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router";
import { getLastPage, clearLastPage } from "../utils/last-page";

export const usePostLoginRedirect = (isLoggedIn: boolean) => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isLoggedIn) {
      // Check if there's a saved last page
      const lastPage = getLastPage();
      if (lastPage) {
        // Don't redirect if the user is already on the saved page
        if (location.pathname !== lastPage) {
          navigate(lastPage);
        }
        clearLastPage();
      }
    }
  }, [isLoggedIn, navigate, location.pathname]);
};
