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
      
      // Only redirect if:
      // 1. There is a saved last page
      // 2. The user is currently on the root page (/) or a generic page
      // 3. The user is not already on the saved page
      const isOnGenericPage = location.pathname === "/" || 
                             location.pathname === "/login" || 
                             location.pathname === "/tos";
      
      if (lastPage && isOnGenericPage && location.pathname !== lastPage) {
        navigate(lastPage);
      }
      
      // Always clear the last page after login, whether we redirected or not
      clearLastPage();
    }
  }, [isLoggedIn, navigate, location.pathname]);
};
