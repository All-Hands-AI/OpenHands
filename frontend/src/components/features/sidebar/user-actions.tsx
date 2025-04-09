import OpenHands from "#/api/open-hands";
import {
  removeAuthTokenHeader,
  setAuthTokenHeader,
} from "#/api/open-hands-axios";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";
import { wagmiConfig } from "#/config/config";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { reduceString } from "#/utils/utils";
import {
  useGetListAddresses,
  useGetPublicKey,
  useGetSignedLogin,
  usePersistActions,
} from "#/zutand-stores/persist-config/selector";
import { useAccountModal, useConnectModal } from "@rainbow-me/rainbowkit";
import { signMessage, disconnect } from "@wagmi/core";
import { useEffect } from "react";
import { FaUserAlt, FaWallet } from "react-icons/fa";
import { twMerge } from "tailwind-merge";
import { useAccount, useAccountEffect } from "wagmi";
import { mainnet } from "wagmi/chains";
import UserIcon from "#/icons/user-icon.svg?react";

interface UserActionsProps {
  onLogout: () => void;
  isLoading?: boolean;
}

export function UserActions({ onLogout, isLoading }: UserActionsProps) {
  const { openConnectModal, connectModalOpen } = useConnectModal();
  const { openAccountModal, accountModalOpen } = useAccountModal();
  const account = useAccount();
  const { setSignedLogin, setPublicKey, setJwt, reset, setListAddresses } =
    usePersistActions();
  const signedLogin = useGetSignedLogin();
  const publicKey = useGetPublicKey();
  const listAddresses = useGetListAddresses();

  const handleLogout = () => {
    removeAuthTokenHeader();
    onLogout();
    disconnect(wagmiConfig);
  };

  useAccountEffect({
    onConnect(account) {
      console.log("Connected!", account);
      onConnectEffect(account);
    },
    onDisconnect() {
      console.log("Disconnected!");
      reset();
      removeAuthTokenHeader();
      handleLogout();
    },
  });

  const onConnectEffect = async (account: any) => {
    try {
      if (account?.address && !signedLogin) {
        const message = "Sign to confirm account access to Thesis Capsule";
        const signature = await signMessage(wagmiConfig, {
          message: message,
        });

        console.log("signature", signature);
        if (signature) {
          try {
            // Verify signature with backend
            const response = await OpenHands.verifySignature(
              signature,
              account?.address,
            );

            // Store user data
            setSignedLogin(signature);
            setPublicKey(response.user.publicAddress);
            setJwt(response.token);
            setAuthTokenHeader(response.token);

            displaySuccessToast("Successfully verified wallet");
          } catch (apiError) {
            console.error("API Error:", apiError);
            reset();
            removeAuthTokenHeader();
            handleLogout();
            throw new Error("Failed to verify wallet with server");
          }
        }
      }
    } catch (error) {
      console.error("Wallet connection error:", error);
      displayErrorToast(
        error instanceof Error ? error.message : "Error connecting wallet",
      );
      reset();
      handleLogout();
      removeAuthTokenHeader();
    }
  };

  return (
    <div data-testid="user-actions" className="w-10 h-10 relative">
      {/* <ConnectButton
        accountStatus={"avatar"}
        showBalance={false}
        chainStatus={"none"}
      /> */}
      {openConnectModal && (
        <button
          onClick={openConnectModal}
          type="button"
          className="w-10 h-10 rounded-full flex items-center justify-center bg-background"
        >
          <FaWallet />
        </button>
      )}

      {openAccountModal && (
        <TooltipButton
          testId="user-avatar"
          tooltip={reduceString(account?.address || "")}
          ariaLabel={reduceString(account?.address || "")}
          onClick={openAccountModal}
          className={twMerge(
            "w-10 h-10 p-2 rounded-lg flex items-center justify-center  text-neutral-800 hover:bg-neutral-1000 hover:text-neutral-100",
            isLoading && "bg-transparent",
            (connectModalOpen || accountModalOpen) &&
              "bg-neutral-1000 text-neutral-100",
          )}
        >
          <UserIcon />
        </TooltipButton>
      )}

      {/* <button onClick={openConnectModal}>
        <UserAvatar
          avatarUrl={user?.avatar_url}
          onClick={toggleAccountMenu}
          isLoading={isLoading}
        />
      </button> */}

      {/* <WalletButton.Custom wallet="rainbow">
        {({ ready, connect }) => {
          return (
            <button type="button" disabled={!ready} onClick={connect}>
              Connect Rainbow
            </button>
          );
        }}
      </WalletButton.Custom> */}

      {/* {accountContextMenuIsVisible && (
        <AccountSettingsContextMenu
          isLoggedIn={!!user}
          onLogout={handleLogout}
          onClose={closeAccountMenu}
        />
      )} */}
    </div>
  );
}
