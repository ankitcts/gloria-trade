export const ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    ME: "/auth/me",
    REFRESH: "/auth/refresh",
    LOGOUT: "/auth/logout",
  },

  // Securities
  SECURITIES: {
    LIST: "/securities",
    DETAIL: (id: string) => `/securities/${id}`,
    SEARCH: "/securities/search",
    HISTORY: (id: string) => `/securities/${id}/history`,
  },

  // Predictions
  PREDICTIONS: {
    LIST: "/predictions",
    DETAIL: (id: string) => `/predictions/${id}`,
    BY_SECURITY: (securityId: string) =>
      `/securities/${securityId}/predictions`,
  },

  // Trading
  TRADING: {
    ORDERS: "/orders",
    ORDER_DETAIL: (id: string) => `/orders/${id}`,
    CANCEL_ORDER: (id: string) => `/orders/${id}/cancel`,
    TRADES: "/trades",
  },

  // Portfolio
  PORTFOLIO: {
    LIST: "/portfolios",
    DETAIL: (id: string) => `/portfolios/${id}`,
    HOLDINGS: (id: string) => `/portfolios/${id}/holdings`,
    TRANSACTIONS: (id: string) => `/portfolios/${id}/transactions`,
  },

  // Notifications
  NOTIFICATIONS: {
    LIST: "/notifications",
    MARK_READ: (id: string) => `/notifications/${id}/read`,
    MARK_ALL_READ: "/notifications/read-all",
  },

  // Admin
  ADMIN: {
    USERS: "/admin",
    USER_DETAIL: (id: string) => `/admin/${id}`,
    USER_ROLE: (id: string) => `/admin/${id}/role`,
    USER_STATUS: (id: string) => `/admin/${id}/status`,
    USER_PERMISSIONS: (id: string) => `/admin/${id}/permissions`,
    USER_GROUPS: (id: string) => `/admin/${id}/groups`,
    GROUPS: "/admin/groups",
    GROUP_DETAIL: (id: string) => `/admin/groups/${id}`,
    GROUP_MEMBERS: (id: string) => `/admin/groups/${id}/members`,
    PERMISSIONS: "/admin/permissions",
  },
} as const;
