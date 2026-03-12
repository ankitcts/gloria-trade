import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import { useAuthStore } from "@/stores/authStore";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from "@/types/auth";

export function useLogin() {
  const login = useAuthStore((s) => s.login);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const response = await apiClient.post<TokenResponse>(
        ENDPOINTS.AUTH.LOGIN,
        data
      );
      return response.data;
    },
    onSuccess: (data) => {
      login({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
      });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      const response = await apiClient.post<User>(
        ENDPOINTS.AUTH.REGISTER,
        data
      );
      return response.data;
    },
  });
}

export function useMe() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setUser = useAuthStore((s) => s.setUser);

  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const response = await apiClient.get<User>(ENDPOINTS.AUTH.ME);
      setUser(response.data);
      return response.data;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}
