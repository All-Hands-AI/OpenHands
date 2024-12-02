import { useQuery } from "@tanstack/react-query";
import React from "react";
import InvariantService from "#/api/invariant-service";

type ResponseData = string;

interface UseGetPolicyConfig {
  onSuccess: (data: ResponseData) => void;
}

export const useGetPolicy = (config?: UseGetPolicyConfig) => {
  const data = useQuery<ResponseData>({
    queryKey: ["policy"],
    queryFn: InvariantService.getPolicy,
  });

  const { isFetching, isSuccess, data: policy } = data;

  React.useEffect(() => {
    if (!isFetching && isSuccess && policy) {
      config?.onSuccess(policy);
    }
  }, [isFetching, isSuccess, policy, config?.onSuccess]);

  return data;
};
