import {
  ConnectPontemAccount,
  PontemWindow,
} from "@pontem/aptos-wallet-adapter";
import { createContext, useContext } from "react";

declare const window: PontemWindow;

export class AuthState {
  connected: boolean;

  token: string | null;

  account: ConnectPontemAccount | null;

  constructor() {
    this.connected = false;

    this.account = null;
    this.token = null;

    if (window.pontem !== null) this.init();
  }

  set_defaults(): AuthState {
    this.connected = false;
    this.account = null;
    this.token = null;

    return this;
  }

  protected async init(): Promise<AuthState> {
    const { pontem } = window;
    if (
      !pontem ||
      !(await pontem.isConnected()) ||
      !this.load_token().check_token()
    )
      return this;

    this.account = await pontem.account();
    this.connected = true;

    return this;
  }

  load_token(): AuthState {
    this.token = localStorage.getItem("wallet_token");
    return this;
  }

  get_new_token(): AuthState {
    // @todo get token from backend
    if (this.account === null)
      throw new Error("There is no connection to the wallet account");
    this.token = crypto.randomUUID();

    localStorage.setItem("wallet_token", this.token);

    return this;
  }

  check_token(): boolean {
    // @todo check token on backend
    return this.token !== null;
  }

  async connect(): Promise<AuthState> {
    const { pontem } = window;
    if (!pontem) return this.set_defaults();

    if (this.connected && this.check_token()) return this;

    if (!(await pontem.isConnected())) {
      this.account = await pontem.connect();
    } else if (this.account === null) {
      this.account = await pontem.account();
    }

    if (!this.check_token()) this.get_new_token();
    if (this.token !== null) this.connected = true;

    return this;
  }

  async disconnect() {
    this.set_defaults();
    const { pontem } = window;
    if (!pontem) return;
    await pontem.disconnect();
  }
}

const AuthContext = createContext<AuthState>(new AuthState());
export const useAuthWallet = (): AuthState => useContext(AuthContext);
