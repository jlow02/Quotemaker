import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { loginUser } from '../api/services';

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

/**
 * @purpose Hook for login/logout workflows.
 *          setAccessToken + navigate called directly in login() — not in onSuccess callback —
 *          to avoid React Query callback / HMR module-split timing issues.
 * @owner [Claude]
 */
export default function useAuth() {
  const navigate = useNavigate();
  const { user, isAuthenticated, setAccessToken, clearAuth } = useAuthStore();

  const { mutateAsync: loginMutation, isPending: isLoading, error } = useMutation<
    AuthTokens,
    Error,
    LoginCredentials
  >({ mutationFn: loginUser });

  const login = async (email: string, password: string) => {
    const data = await loginMutation({ username: email, password });
    setAccessToken(data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('refreshToken', data.refresh_token);
    }
    navigate('/');
  };

  const logout = () => {
    clearAuth();
    navigate('/login');
  };

  return { user, isAuthenticated, login, logout, isLoading, error };
}
