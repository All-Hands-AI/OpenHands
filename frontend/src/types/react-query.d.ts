import "@tanstack/react-query";
import type { AxiosError } from "axios";

interface MyMeta extends Record<string, unknown> {
  disableToast?: boolean;
}

declare module "@tanstack/react-query" {
  interface Register {
    defaultError: AxiosError;

    queryMeta: MyMeta;
    mutationMeta: MyMeta;
  }
}
