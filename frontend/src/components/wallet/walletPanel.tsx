import "./wallet.css";
import { useAuthWallet } from "#/hooks/use-auth";
import { WalletButton } from "./wallet";
import { WalletBalance } from "./walletBalance";
import { WalletUpBalance } from "./walletUpBalance";

export function WalletPanel() {
  const auth = useAuthWallet();

  console.log(auth.connected);
  return (
    <div className="wallet_panel">
      {auth.connected && <WalletBalance />}
      {auth.connected && <WalletUpBalance />}
      <WalletButton />
    </div>
  );
}
