import "./auth_wallet.css";

export function WalletPage() {
  const text = [
    "To access it, you must log in via the Pontem wallet.",
    "To install, visit the ",
    "page",
  ];

  return (
    <div id="wallet_page">
      <p>{text[0]}</p>
      <p>
        {text[1]}
        <a href="https://pontem.network/pontem-wallet">{text[2]}</a>
      </p>
    </div>
  );
}
