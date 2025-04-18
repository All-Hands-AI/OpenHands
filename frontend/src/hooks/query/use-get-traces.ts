import { useQuery } from "@tanstack/react-query";
import React from "react";
import InvariantService from "#/api/invariant-service";

type ResponseData = object;

interface UseGetTracesConfig {
  onSuccess: (data: ResponseData) => void;
}

export const useGetTraces = (config?: UseGetTracesConfig) => {
  const data = useQuery({
    queryKey: ["traces"],
    queryFn: InvariantService.getTraces,
    enabled: false,
  });

  const { isFetching, isSuccess, data: traces } = data;

  React.useEffect(() => {
    if (!isFetching && isSuccess && traces) {
      config?.onSuccess(traces);
    }
  }, [isFetching, isSuccess, traces, config?.onSuccess]);

  return data;
};
