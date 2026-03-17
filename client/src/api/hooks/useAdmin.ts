import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/api/client";
import { ENDPOINTS } from "@/api/endpoints";
import type {
  AdminUserDetail,
  PaginatedResponse,
  User,
  UserGroup,
} from "@/types/auth";

// ---- Users ----

export function useAdminUsers(
  page = 1,
  pageSize = 20,
  roleFilter?: string,
  statusFilter?: string,
  search?: string
) {
  return useQuery({
    queryKey: ["admin", "users", page, pageSize, roleFilter, statusFilter, search],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<User>>(
        ENDPOINTS.ADMIN.USERS,
        {
          params: {
            page,
            page_size: pageSize,
            ...(roleFilter && { role: roleFilter }),
            ...(statusFilter && { status: statusFilter }),
            ...(search && { search }),
          },
        }
      );
      return response.data;
    },
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      email: string;
      password: string;
      first_name: string;
      last_name: string;
      role: string;
      account_status: string;
      phone?: string;
    }) => {
      const response = await apiClient.post(ENDPOINTS.ADMIN.USERS, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useAdminUserDetail(userId: string) {
  return useQuery({
    queryKey: ["admin", "users", userId],
    queryFn: async () => {
      const response = await apiClient.get<AdminUserDetail>(
        ENDPOINTS.ADMIN.USER_DETAIL(userId)
      );
      return response.data;
    },
    enabled: !!userId,
  });
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      const response = await apiClient.patch(
        ENDPOINTS.ADMIN.USER_ROLE(userId),
        { role }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useUpdateUserStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      status,
    }: {
      userId: string;
      status: string;
    }) => {
      const response = await apiClient.patch(
        ENDPOINTS.ADMIN.USER_STATUS(userId),
        { account_status: status }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useUpdateUserPermissions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      permissions,
    }: {
      userId: string;
      permissions: string[];
    }) => {
      const response = await apiClient.patch(
        ENDPOINTS.ADMIN.USER_PERMISSIONS(userId),
        { extra_permissions: permissions }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useUpdateUserGroups() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      groupIds,
    }: {
      userId: string;
      groupIds: string[];
    }) => {
      const response = await apiClient.patch(
        ENDPOINTS.ADMIN.USER_GROUPS(userId),
        { group_ids: groupIds }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string) => {
      const response = await apiClient.delete(
        ENDPOINTS.ADMIN.USER_DETAIL(userId)
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

// ---- Groups ----

export function useGroups() {
  return useQuery({
    queryKey: ["admin", "groups"],
    queryFn: async () => {
      const response = await apiClient.get<UserGroup[]>(
        ENDPOINTS.ADMIN.GROUPS
      );
      return response.data;
    },
  });
}

export function useCreateGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      name: string;
      description: string | null;
      permissions: string[];
    }) => {
      const response = await apiClient.post<UserGroup>(
        ENDPOINTS.ADMIN.GROUPS,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "groups"] });
    },
  });
}

export function useUpdateGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      groupId,
      data,
    }: {
      groupId: string;
      data: { name?: string; description?: string | null; permissions?: string[] };
    }) => {
      const response = await apiClient.patch<UserGroup>(
        ENDPOINTS.ADMIN.GROUP_DETAIL(groupId),
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "groups"] });
    },
  });
}

export function useDeleteGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (groupId: string) => {
      const response = await apiClient.delete(
        ENDPOINTS.ADMIN.GROUP_DETAIL(groupId)
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "groups"] });
    },
  });
}

export function useAddGroupMembers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      groupId,
      memberIds,
    }: {
      groupId: string;
      memberIds: string[];
    }) => {
      const response = await apiClient.post(
        ENDPOINTS.ADMIN.GROUP_MEMBERS(groupId),
        { member_ids: memberIds }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "groups"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useRemoveGroupMembers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      groupId,
      memberIds,
    }: {
      groupId: string;
      memberIds: string[];
    }) => {
      const response = await apiClient.delete(
        ENDPOINTS.ADMIN.GROUP_MEMBERS(groupId),
        { data: { member_ids: memberIds } }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "groups"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

// ---- Permissions ----

export function usePermissions() {
  return useQuery({
    queryKey: ["admin", "permissions"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>(
        ENDPOINTS.ADMIN.PERMISSIONS
      );
      return response.data;
    },
  });
}
