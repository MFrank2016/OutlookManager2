import { useQuery } from "@tanstack/react-query";

import api, { buildV2AccountPath } from "@/lib/api";
import { AccountHealth } from "@/types";

export function useAccountHealth(email: string | null, enabled = true) {
  return useQuery({
    queryKey: ["account-health", email],
    queryFn: async () => {
      if (!email) {
        return null;
      }
      const { data } = await api.get<AccountHealth>(buildV2AccountPath(email, "/health"));
      return data;
    },
    enabled: enabled && !!email,
    staleTime: 30 * 1000,
  });
}
