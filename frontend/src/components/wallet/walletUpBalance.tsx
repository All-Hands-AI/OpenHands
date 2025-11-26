import { useAuthWallet } from "#/hooks/use-auth";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import "./wallet.css";

export function WalletUpBalance() {
  const upText = "top up balance";

  const auth = useAuthWallet();
  const topUpBalance = async () => {
    try {
      await auth.topUpBalance();
    } catch (error: unknown) {
      displayErrorToast((error as Error).message);
    }
  };

  // topUpBalance();

  return (
    <button className="top_up_balance" type="button" onClick={topUpBalance}>
      {upText}
    </button>
  );
}
