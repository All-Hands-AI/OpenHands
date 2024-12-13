import { useQuery } from "@tanstack/react-query";
import axios from "axios";

export const useServedApp = () =>
  useQuery({
    queryKey: ["served-app"],
    queryFn: async () => axios.get("http://localhost:4141"),
    refetchInterval: 3000,
  });
