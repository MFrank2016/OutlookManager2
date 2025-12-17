import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface AccountsFilterState {
  page: number;
  pageSize: number;
  search: string;
  includeTags: string;
  excludeTags: string;
  refreshStatus?: string;
  setFilters: (partial: Partial<AccountsFilterState>) => void;
  reset: () => void;
}

const initialState: Omit<AccountsFilterState, "setFilters" | "reset"> = {
  page: 1,
  pageSize: 10,
  search: "",
  includeTags: "",
  excludeTags: "",
  refreshStatus: undefined,
};

export const useAccountsFilterStore = create<AccountsFilterState>()(
  persist(
    (set) => ({
      ...initialState,
      setFilters: (partial) =>
        set((state) => ({
          ...state,
          ...partial,
        })),
      reset: () => set(() => ({ ...initialState })),
    }),
    {
      name: "accounts-filters-storage",
      storage: createJSONStorage(() => localStorage),
    }
  )
);


