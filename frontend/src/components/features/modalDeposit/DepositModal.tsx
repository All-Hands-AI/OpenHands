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
      <div
        className="fixed inset-0 bg-gray-300/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative w-full max-w-md overflow-hidden rounded-xl bg-gray-300 border border-gray-500/30 shadow-2xl">
        {/* Header */}
        <div className="bg-gray-300 px-6 py-4 flex items-center justify-between border-b border-gray-500/20">
          <h2 className="text-xl font-semibold text-content flex items-center">
            <span className="mr-2 text-primary">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                <path
                  fillRule="evenodd"
                  d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z"
                  clipRule="evenodd"
                />
              </svg>
            </span>
            Deposit
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-tertiary-light hover:bg-tertiary/10 hover:text-primary transition-colors"
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {/* Network Selection Tabs */}
          <div className="mb-6">
            <div className="flex space-x-2 rounded-xl bg-gray-100/50 p-1.5 shadow-inner">
              {NETWORKS.map((network) => (
                <button
                  key={network.chainId}
                  onClick={() => setSelectedNetwork(network)}
                  className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2.5 transition-all ${
                    selectedNetwork?.chainId === network.chainId
                      ? "bg-primary text-base-secondary shadow-lg font-semibold"
                      : "text-tertiary-light hover:bg-gray-400/50"
                  }`}
                >
                  {/* Network icon would go here if enabled */}
                  <span className="font-medium">{network.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* QR Code and Address Section */}
          {selectedNetwork && (
            <div className="rounded-xl bg-gray-300 p-6 shadow-inner">
              {/* QR Code */}
              <div className="mb-6 flex justify-center">
                {qrUrl ? (
                  <div className="p-3 bg-content-2 rounded-lg shadow-md">
                    <img
                      src={qrUrl}
                      alt="QR Code"
                      className="h-48 w-48 rounded-md"
                    />
                  </div>
                ) : (
                  <div className="h-48 w-48 rounded-lg bg-gray-400 animate-pulse"></div>
                )}
              </div>

              {/* Deposit Address */}
              <div>
                <div className="mb-3 flex items-center gap-2 text-sm text-tertiary-light">
                  <svg
                    className="h-5 w-5 text-primary"
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
                  <span className="font-medium">Deposit Address</span>
                </div>
                <div className="group relative">
                  <div className="flex items-center justify-between rounded-lg bg-base p-3.5 text-sm border border-gray-500/20">
                    <span className="text-content-2 font-mono">
                      {reduceString(
                        listAddresses[selectedNetwork.chainId],
                        8,
                        8,
                      )}
                    </span>
                    <button
                      onClick={() =>
                        handleCopy(listAddresses[selectedNetwork.chainId])
                      }
                      className="text-tertiary-light hover:text-primary transition-colors"
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
                    <div className="absolute -top-8 right-0 rounded-md bg-success px-3 py-1.5 text-xs text-base-secondary font-medium shadow-lg transition-all">
                      Copied!
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-6 text-xs text-tertiary-light text-center">
                Only send {selectedNetwork.name} assets to this address. Other
                assets may be lost.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DepositModal;
