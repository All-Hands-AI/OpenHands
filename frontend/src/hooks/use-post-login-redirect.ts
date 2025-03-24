import { useEffect } from "react";
import { useNavigate } from "react-router";
import { getLastPage, clearLastPage } from "../utils/last-page";

export const usePostLoginRedirect = (isLoggedIn: boolean) => {
  const navigate = useNavigate();

  useEffect(() => {
    if (isLoggedIn) {
      const lastPage = getLastPage();
      if (lastPage) {
        navigate(lastPage);
        clearLastPage();
      }
    }
  }, [isLoggedIn, navigate]);
};
