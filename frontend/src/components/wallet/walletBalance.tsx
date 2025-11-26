import { useEffect, useState } from "react";
import "./wallet.css";
import { useAuthWallet } from "#/hooks/use-auth";

// @todo
const UPDATE_INTERVAL = 5000;

export function WalletDisplayBalance() {
  const balanceLabelText = "balance";
  const coinName = "Lum";

  const auth = useAuthWallet();
  const [balance, setBalance] = useState(0.0);

  useEffect(() => {
    const interval: NodeJS.Timeout = setInterval(
      () => auth.balance().then(setBalance),
      UPDATE_INTERVAL,
    );
    auth.balance().then(setBalance);

    return () => {
      if (interval !== null) clearInterval(interval);
    };
  }, [auth]);

  return (
    <div className="wallet_view_balance">
      <span className="label">{balanceLabelText}:</span>
      <span className="value">
        {balance} {coinName}
      </span>
    </div>
  );
}
