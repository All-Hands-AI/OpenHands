import React from "react";
import { Button } from "@nextui-org/react";
import { useOAuth2 } from "@tasoskakour/react-use-oauth2";
import { GrGithub, GrGoogle } from "react-icons/gr";
import { FaUserCircle } from "react-icons/fa";
import BaseModal from "#/components/modals/base-modal/BaseModal";
import { fetchTokenByCode, fetchToken } from "#/services/auth";
import toast from "#/utils/toast";

interface SigninProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

function SigninModal({ isOpen, onOpenChange }: SigninProps) {
  const onSuccess = (token: string) => {
    localStorage.setItem("token", token);
    toast.info("Sign in success");
    onOpenChange(false);
  };
  const onError = (err: string) => {
    toast.error(`Sign in failed: ${err}`);
  };

  const { loading: githubLoading, getAuth: getGithubAuth } = useOAuth2({
    authorizeUrl: "https://github.com/login/oauth/authorize",
    clientId: import.meta.env.VITE_GITHUB_CLIENT_ID || "", // TODO: get the configurations from backend.
    redirectUri: "http://localhost:3001/auth/callback",
    scope: "read:user",
    responseType: "code",
    exchangeCodeForTokenQueryFn: async (callbackParameters) => {
      const res = await fetchTokenByCode("github", callbackParameters.code);
      return res.token;
    },
    onSuccess,
    onError,
  });

  const { loading: googleLoading, getAuth: getGoogleAuth } = useOAuth2({
    authorizeUrl: "https://accounts.google.com/o/oauth2/auth",
    clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || "", // TODO: get the configurations from backend.
    redirectUri: "http://localhost:3001/auth/callback",
    scope: "openid profile email",
    responseType: "code",
    exchangeCodeForTokenQueryFn: async (callbackParameters) => {
      const res = await fetchTokenByCode("google", callbackParameters.code);
      return res.token;
    },
    onSuccess,
    onError,
  });

  const getToken = async () => {
    try {
      const data = await fetchToken();
      onSuccess(data.token);
    } catch (error) {
      onError(String(error));
    }
  };

  return (
    <BaseModal isOpen={isOpen} title="Sign in" onOpenChange={onOpenChange}>
      <Button onClick={getToken} startContent={<FaUserCircle size={20} />}>
        Refresh Guest Info
      </Button>
      <Button
        disabled={githubLoading || googleLoading}
        onClick={getGithubAuth}
        startContent={<GrGithub size={20} />}
      >
        Sign in with GitHub
      </Button>
      <Button
        disabled={githubLoading || googleLoading}
        onClick={getGoogleAuth}
        startContent={<GrGoogle size={20} />}
      >
        Sign in with Google
      </Button>
    </BaseModal>
  );
}

export default SigninModal;
