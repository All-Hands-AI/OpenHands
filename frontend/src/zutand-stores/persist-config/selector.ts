import usePersistStore from "./usePersistStore";

export const usePersistActions = () =>
  usePersistStore((state) => state.actions);
export const useGetSignedLogin = () =>
  usePersistStore((state) => state.signedLogin);
export const useGetPublicKey = () =>
  usePersistStore((state) => state.publicKey);
export const useGetListAddresses = () =>
  usePersistStore((state) => state.listAddresses);
export const useGetJwt = () => usePersistStore((state) => state.jwt);
