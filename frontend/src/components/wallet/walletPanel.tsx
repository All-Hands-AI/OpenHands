import "./wallet.css";
import { useAuthWallet } from "#/hooks/use-auth";
import { WalletButton } from "./wallet";
import { WalletDisplayBalance } from "./walletBalance";
import { WalletUpBalance } from "./walletUpBalance";

export function WalletPanel() {
  const auth = useAuthWallet();

  return (
    <div className="wallet_panel">
      {auth.connected && <WalletDisplayBalance />}
      {auth.connected && <WalletUpBalance />}
      <WalletButton />
    </div>
  );
}
