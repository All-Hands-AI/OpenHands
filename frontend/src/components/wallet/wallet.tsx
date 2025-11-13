import "./wallet.css";
import { useReducer } from "react";
import { useLocation, useNavigate } from "react-router";
import { useAuthWallet } from "#/hooks/use-auth";

function Icon() {
  return (
    <svg
      height="512"
      viewBox="0 0 512 512"
      width="512"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="m480 264h-8v-104a8 8 0 0 0 -8-8h-24v-72a8 8 0 0 0 -8-8h-376a48.051 48.051 0 0 0 -48 48v272a48.051 48.051 0 0 0 48 48h408a8 8 0 0 0 8-8v-104h8a24.032 24.032 0 0 0 24-24v-16a24.032 24.032 0 0 0 -24-24zm-424-176h368v64h-368a32 32 0 0 1 0-64zm400 336h-400a32.042 32.042 0 0 1 -32-32v-236.26a47.8 47.8 0 0 0 32 12.26h400v96h-24a8 8 0 0 0 -8 8v48a8 8 0 0 0 8 8h24zm32-120a8.011 8.011 0 0 1 -8 8h-40v-32h40a8.011 8.011 0 0 1 8 8z" />
      <path d="m432 392h-120a8 8 0 0 0 0 16h120a8 8 0 0 0 0-16z" />
      <path d="m400 368a8 8 0 0 0 0 16h32a8 8 0 0 0 0-16z" />
    </svg>
  );
}

export function WalletButton() {
  const auth = useAuthWallet();
  const forceUpdate = useReducer((x) => x + 1, 0)[1];
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const buttonText = { connect: "Connect", disconnect: "Disconnect" };

  if (!auth.connected) {
    return (
      <button
        className="pontem_wallet connect"
        type="button"
        onClick={async () => {
          await auth.connect();
          if (auth.connected && pathname === "/auth") navigate("/");
          else forceUpdate();
        }}
      >
        <Icon />
        {buttonText.connect}
      </button>
    );
  }

  return (
    <button
      className="pontem_wallet disconnect"
      type="button"
      onClick={async () => {
        await auth.disconnect();
        if (!auth.connected && pathname !== "/auth") navigate("/auth");
        else forceUpdate();
      }}
    >
      <Icon />
      {buttonText.disconnect}
    </button>
  );
}
