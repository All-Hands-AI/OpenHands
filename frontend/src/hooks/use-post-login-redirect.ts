import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router";
import { getLastPage, clearLastPage } from "../utils/last-page";

export const usePostLoginRedirect = (isLoggedIn: boolean) => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isLoggedIn) {
      // Only redirect to last page if user is on the root page
      if (location.pathname === "/") {
        const lastPage = getLastPage();
        if (lastPage) {
          navigate(lastPage);
          clearLastPage();
        }
      }
    }
  }, [isLoggedIn, navigate, location.pathname]);
};
