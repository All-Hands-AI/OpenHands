import "./wallet.css";

export function WalletBalance() {
  const balanceLabelText = "balance";
  const coinName = "Lum";
  console.log("@todo balance");

  return (
    <div className="wallet_view_balance">
      <span className="label">{balanceLabelText}:</span>
      <span className="value">0 {coinName}</span>
    </div>
  );
}
