import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { User } from "@/types";
import api from "@/lib/api";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (token, user) => {
        localStorage.setItem("auth_token", token);
        set({ token, user, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        set({ token: null, user: null, isAuthenticated: false });
      },
      fetchUser: async () => {
        try {
           // Fetch current user from /auth/me
           const response = await api.get<User>("/auth/me");
           set({ user: response.data, isAuthenticated: true });
        } catch (error) {
           // If fetch fails (e.g. 401), logout logic in interceptor handles it, 
           // but we can also ensure state is cleared here if needed.
           console.error("Failed to fetch user", error);
           set({ user: null, isAuthenticated: false });
        }
      }
    }),
    {
      name: "auth-storage", // unique name
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token, user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

