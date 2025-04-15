import { useQuery } from "@tanstack/react-query";
import React from "react";
import InvariantService from "#/api/invariant-service";

type ResponseData = number;

interface UseGetRiskSeverityConfig {
  onSuccess: (data: ResponseData) => void;
}

export const useGetRiskSeverity = (config?: UseGetRiskSeverityConfig) => {
  const data = useQuery<ResponseData>({
    queryKey: ["risk_severity"],
    queryFn: InvariantService.getRiskSeverity,
  });

  const { isFetching, isSuccess, data: riskSeverity } = data;

  React.useEffect(() => {
    if (!isFetching && isSuccess && riskSeverity) {
      config?.onSuccess(riskSeverity);
    }
  }, [isFetching, isSuccess, riskSeverity, config?.onSuccess]);

  return data;
};
