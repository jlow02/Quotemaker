import { create, StoreApi, UseBoundStore } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * @purpose Defines the structure for a user in the application.
 * @owner [Gemini]
 */
interface User {
  id: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

/**
 * @purpose Defines the authentication state managed by the Zustand store.
 * @owner [Gemini]
 */
interface AuthState {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
}

/**
 * @purpose Defines the actions available to modify the authentication state.
 * @owner [Gemini]
 */
interface AuthActions {
  setAccessToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  clearAuth: () => void;
}

/**
 * @purpose Combined type for the authentication store, including state and actions.
 * @owner [Gemini]
 */
type AuthStore = AuthState & AuthActions;

const REFRESH_TOKEN_KEY = 'refreshToken';

/**
 * @purpose The main Zustand store for managing authentication state.
 *          Persisted to localStorage so auth survives page reloads.
 * @owner [Claude]
 */
const authStore = create<AuthStore>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      isAuthenticated: false,

      setAccessToken: (token: string | null): void => {
        set({ accessToken: token, isAuthenticated: !!token });
      },

      setUser: (user: User | null): void => {
        set({ user });
      },

      clearAuth: (): void => {
        set({ accessToken: null, user: null, isAuthenticated: false });
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      },
    }),
    {
      name: 'nextan-auth',
      // Only persist the token — not actions (they're functions and can't be serialised)
      partialize: (state) => ({
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    }
  )
);

export const useAuthStore: UseBoundStore<StoreApi<AuthStore>> = authStore;

export function getAuthState(): AuthState & AuthActions {
  return authStore.getState();
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string): void {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function clearRefreshToken(): void {
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}
