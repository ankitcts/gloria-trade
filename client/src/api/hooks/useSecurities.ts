import { useQuery } from "@tanstack/react-query";
import apiClient from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import type { Security, SecurityDetail, PriceHistory } from "@/types/security";

export function useSecurities(page = 1, limit = 20) {
  return useQuery({
    queryKey: ["securities", page, limit],
    queryFn: async () => {
      const response = await apiClient.get<{
        items: Security[];
        total: number;
        page: number;
        limit: number;
      }>(ENDPOINTS.SECURITIES.LIST, {
        params: { page, limit },
      });
      return response.data;
    },
  });
}

export function useSecuritySearch(query: string) {
  return useQuery({
    queryKey: ["securities", "search", query],
    queryFn: async () => {
      const response = await apiClient.get<Security[]>(
        ENDPOINTS.SECURITIES.SEARCH,
        { params: { q: query } }
      );
      return response.data;
    },
    enabled: query.length >= 2,
  });
}

export function useSecurityDetail(id: string) {
  return useQuery({
    queryKey: ["securities", id],
    queryFn: async () => {
      const response = await apiClient.get<SecurityDetail>(
        ENDPOINTS.SECURITIES.DETAIL(id)
      );
      return response.data;
    },
    enabled: !!id,
  });
}

export function useSecurityHistory(
  id: string,
  params?: { start_date?: string; end_date?: string; interval?: string }
) {
  return useQuery({
    queryKey: ["securities", id, "history", params],
    queryFn: async () => {
      const response = await apiClient.get<PriceHistory[]>(
        ENDPOINTS.SECURITIES.HISTORY(id),
        { params }
      );
      return response.data;
    },
    enabled: !!id,
  });
}
