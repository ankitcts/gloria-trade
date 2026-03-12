import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  Divider,
  useTheme,
  Avatar,
} from "@mui/material";
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  ShowChart as SecuritiesIcon,
  Psychology as PredictionsIcon,
  SwapHoriz as TradingIcon,
  AccountBalance as PortfolioIcon,
  Notifications as NotificationsIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
} from "@mui/icons-material";
import { useAuthStore } from "@/stores/authStore";
import { useThemeStore } from "@/stores/themeStore";

const DRAWER_WIDTH = 260;

const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "Securities", path: "/securities", icon: <SecuritiesIcon /> },
  { label: "Predictions", path: "/predictions", icon: <PredictionsIcon /> },
  { label: "Trading", path: "/trading", icon: <TradingIcon /> },
  { label: "Portfolio", path: "/portfolio", icon: <PortfolioIcon /> },
  {
    label: "Notifications",
    path: "/notifications",
    icon: <NotificationsIcon />,
  },
];

export default function AppShell() {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const toggleTheme = useThemeStore((s) => s.toggleTheme);
  const themeMode = useThemeStore((s) => s.mode);

  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleDrawerToggle = () => setMobileOpen(!mobileOpen);
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) =>
    setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    handleMenuClose();
    logout();
    navigate("/login");
  };

  const drawerContent = (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Logo */}
      <Box
        sx={{
          p: 2.5,
          display: "flex",
          alignItems: "center",
          gap: 1.5,
        }}
      >
        <Box
          sx={{
            width: 36,
            height: 36,
            borderRadius: 1,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.warning.main})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 800,
            fontSize: "1.1rem",
            color: "#000",
          }}
        >
          GT
        </Box>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.warning.main})`,
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          Gloria Trade
        </Typography>
      </Box>

      <Divider sx={{ borderColor: "rgba(255,255,255,0.06)" }} />

      {/* Navigation */}
      <List sx={{ flex: 1, px: 1.5, pt: 1.5 }}>
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.path === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.path);

          return (
            <ListItemButton
              key={item.path}
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
              selected={isActive}
              sx={{
                borderRadius: 1.5,
                mb: 0.5,
                "&.Mui-selected": {
                  backgroundColor: "rgba(255, 179, 0, 0.12)",
                  "&:hover": {
                    backgroundColor: "rgba(255, 179, 0, 0.18)",
                  },
                  "& .MuiListItemIcon-root": {
                    color: "warning.main",
                  },
                  "& .MuiListItemText-primary": {
                    color: "warning.main",
                    fontWeight: 600,
                  },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          );
        })}
      </List>

      {/* User info at bottom */}
      <Divider sx={{ borderColor: "rgba(255,255,255,0.06)" }} />
      <Box sx={{ p: 2, display: "flex", alignItems: "center", gap: 1.5 }}>
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: "primary.main",
            fontSize: "0.85rem",
          }}
        >
          {user?.first_name?.[0] || user?.username?.[0] || "U"}
        </Avatar>
        <Box sx={{ overflow: "hidden" }}>
          <Typography variant="body2" fontWeight={600} noWrap>
            {user?.first_name
              ? `${user.first_name} ${user.last_name}`
              : user?.username || "User"}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            noWrap
            display="block"
          >
            {user?.email || ""}
          </Typography>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      {/* AppBar */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          backgroundColor: "background.paper",
          borderBottom: "1px solid",
          borderColor: "divider",
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: "none" } }}
          >
            <MenuIcon />
          </IconButton>

          <Box sx={{ flexGrow: 1 }} />

          {/* Theme toggle */}
          <IconButton onClick={toggleTheme} sx={{ mr: 1 }}>
            {themeMode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>

          {/* User menu */}
          <IconButton onClick={handleMenuOpen}>
            <Avatar
              sx={{
                width: 32,
                height: 32,
                bgcolor: "primary.main",
                fontSize: "0.85rem",
              }}
            >
              {user?.first_name?.[0] || "U"}
            </Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: "right", vertical: "top" }}
            anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
          >
            <MenuItem disabled>
              <ListItemIcon>
                <PersonIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>
                {user?.username || "Profile"}
              </ListItemText>
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Logout</ListItemText>
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer - Mobile */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: "block", md: "none" },
          "& .MuiDrawer-paper": {
            boxSizing: "border-box",
            width: DRAWER_WIDTH,
            backgroundColor: "background.paper",
            borderRight: "1px solid",
            borderColor: "divider",
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Sidebar Drawer - Desktop */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: "none", md: "block" },
          "& .MuiDrawer-paper": {
            boxSizing: "border-box",
            width: DRAWER_WIDTH,
            backgroundColor: "background.paper",
            borderRight: "1px solid",
            borderColor: "divider",
          },
        }}
        open
      >
        {drawerContent}
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: "64px",
          p: 3,
          overflow: "auto",
          backgroundColor: "background.default",
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
