import { useState, useEffect } from "react";
import QRCode from "qrcode";
import {
  useGetJwt,
  useGetListAddresses,
  usePersistActions,
} from "#/zutand-stores/persist-config/selector";
import { reduceString } from "#/utils/utils";
import OpenHands from "#/api/open-hands";
import { useAccount } from "wagmi";

interface Token {
  name: string;
  icon: string;
  coinGeckoId: string;
}

interface Network {
  chainId: string;
  name: string;
  icon: string;
}

interface DepositModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Example networks - replace with your actual networks
const NETWORKS: Network[] = [
  {
    chainId: "evm",
    name: "EVM",
    icon: "/eth-icon.png",
  },
  // {
  //   chainId: "56",
  //   name: "BSC",
  //   icon: "/bnb-icon.png",
  // },
  {
    chainId: "solana",
    name: "Solana",
    icon: "/polygon-icon.png",
  },
];

const DepositModal = ({ isOpen, onClose }: DepositModalProps) => {
  const [selectedNetwork, setSelectedNetwork] = useState<Network | null>(
    NETWORKS[0],
  );
  const [qrUrl, setQrUrl] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const listAddresses = useGetListAddresses();
  const jwt = useGetJwt();
  const { setListAddresses } = usePersistActions();

  useEffect(() => {
    if (selectedNetwork?.chainId && listAddresses[selectedNetwork.chainId]) {
      QRCode.toDataURL(listAddresses[selectedNetwork.chainId])
        .then((url: string) => setQrUrl(url))
        .catch((err: Error) => console.error("Error generating QR code:", err));
    }
  }, [selectedNetwork, listAddresses]);

  useEffect(() => {
    const getGeneratedUserAddress = async () => {
      if (!!listAddresses["solana"] && !!listAddresses["evm"]) {
        return;
      }

      const [evmAddress, solanaAddress] = await Promise.all([
        OpenHands.getAddressByNetwork("evm"),
        OpenHands.getAddressByNetwork("solana"),
      ]);

      setListAddresses({
        ...listAddresses,
        evm: evmAddress,
        solana: solanaAddress,
      });
    };
    getGeneratedUserAddress();
  }, [jwt, selectedNetwork]);

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      <div className="relative w-full max-w-md rounded-2xl bg-base p-6 shadow-xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-content">Deposit</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-content hover:bg-tertiary"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Network Selection Tabs */}
        <div className="mb-6">
          <div className="flex space-x-2 rounded-xl bg-base-secondary p-1.5">
            {NETWORKS.map((network) => (
              <button
                key={network.chainId}
                onClick={() => setSelectedNetwork(network)}
                className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 transition-all ${
                  selectedNetwork?.chainId === network.chainId
                    ? "bg-primary text-base-secondary shadow-lg font-semibold"
                    : "text-tertiary-light hover:bg-tertiary/20"
                }`}
              >
                {/* <img
                  src={network.icon}
                  alt={network.name}
                  className="h-5 w-5 rounded-full"
                /> */}
                <span className="font-medium">{network.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* QR Code and Address Section */}
        {selectedNetwork && (
          <div className="rounded-xl bg-base-secondary p-6">
            {/* QR Code */}
            <div className="mb-6 flex justify-center">
              {qrUrl && (
                <img
                  src={qrUrl}
                  alt="QR Code"
                  className="h-48 w-48 rounded-lg bg-white p-2"
                />
              )}
            </div>

            {/* Deposit Address */}
            <div className="mb-4">
              <div className="mb-2 flex items-center gap-2 text-sm text-tertiary-light">
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 10h4v4h-4v-4z"
                  />
                </svg>
                Deposit Address
              </div>
              <div className="group relative">
                <div className="flex items-center justify-between rounded-lg bg-base p-3 text-sm">
                  <span className="text-content-2">
                    {reduceString(listAddresses[selectedNetwork.chainId], 8, 8)}
                  </span>
                  <button
                    onClick={() =>
                      handleCopy(listAddresses[selectedNetwork.chainId])
                    }
                    className="text-tertiary-light hover:text-primary"
                  >
                    <svg
                      className="h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                      />
                    </svg>
                  </button>
                </div>
                {copied && (
                  <div className="absolute -top-8 right-0 rounded bg-success/80 px-2 py-1 text-xs text-base-secondary">
                    Copied!
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DepositModal;
