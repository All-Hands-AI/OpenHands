import { create } from "zustand";
import { persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

interface PersistStore {
  signedLogin: string;
  publicKey: string;
  listAddresses: Record<string, string>;
  jwt: string;
}

export interface MultisigAction {
  setSignedLogin: (signedLogin: string) => void;
  setPublicKey: (publicKey: string) => void;
  setListAddresses: (listAddresses: Record<string, string>) => void;
  setJwt: (jwt: string) => void;
  reset: () => void;
}

const initialState = {
  signedLogin: "",
  publicKey: "",
  listAddresses: {},
  jwt: "",
};

const usePersistStore = create<PersistStore & { actions: MultisigAction }>()(
  persist(
    immer((set) => ({
      //States
      ...initialState,

      //Actions
      actions: {
        setSignedLogin: (signedLogin: string) => set({ signedLogin }),
        setPublicKey: (publicKey: string) => set({ publicKey }),
        setListAddresses: (listAddresses: Record<string, string>) =>
          set({ listAddresses }),
        setJwt: (jwt: string) => {
          set({ jwt });
        },
        reset: () => {
          set((state) => ({
            signedLogin: "",
            publicKey: "",
            listAddresses: {},
            jwt: "",
            actions: state.actions,
          }));
        },
      },
    })),
    {
      name: "Zus:ThesisCapsule",
      partialize: ({ signedLogin, publicKey, listAddresses, jwt }) => ({
        signedLogin,
        publicKey,
        listAddresses,
        jwt,
      }),
    },
  ),
);

export default usePersistStore;
