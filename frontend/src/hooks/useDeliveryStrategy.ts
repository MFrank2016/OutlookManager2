import { useQuery } from "@tanstack/react-query";

import api, { buildV2AccountPath } from "@/lib/api";
import { DeliveryStrategy, ProviderOverride, StrategyMode } from "@/types";

interface DeliveryStrategyParams {
  email: string | null;
  overrideProvider?: ProviderOverride;
  strategyMode?: StrategyMode;
  skipCache?: boolean;
  enabled?: boolean;
}

export function useDeliveryStrategy({
  email,
  overrideProvider = "auto",
  strategyMode = "auto",
  skipCache = false,
  enabled = true,
}: DeliveryStrategyParams) {
  return useQuery({
    queryKey: [
      "delivery-strategy",
      email,
      overrideProvider,
      strategyMode,
      skipCache,
    ],
    queryFn: async () => {
      if (!email) {
        return null;
      }

      const params: Record<string, unknown> = {};
      if (overrideProvider !== "auto") {
        params.override_provider = overrideProvider;
      }
      if (strategyMode !== "auto") {
        params.strategy_mode = strategyMode;
      }
      if (skipCache) {
        params.skip_cache = true;
      }

      const { data } = await api.get<DeliveryStrategy>(
        buildV2AccountPath(email, "/delivery-strategy"),
        { params }
      );
      return data;
    },
    enabled: enabled && !!email,
    staleTime: 15 * 1000,
  });
}
