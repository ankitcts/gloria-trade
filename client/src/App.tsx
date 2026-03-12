import { useMemo } from "react";
import { Routes, Route } from "react-router-dom";
import { ThemeProvider, CssBaseline, createTheme } from "@mui/material";
import { useThemeStore } from "@/stores/themeStore";

// Layout
import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/common/ProtectedRoute";

// Pages
import Login from "@/pages/Auth/Login";
import Register from "@/pages/Auth/Register";
import Dashboard from "@/pages/Dashboard";
import Securities from "@/pages/Securities";
import Predictions from "@/pages/Predictions";
import Trading from "@/pages/Trading";
import Portfolio from "@/pages/Portfolio";
import Notifications from "@/pages/Notifications";

function App() {
  const mode = useThemeStore((s) => s.mode);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          ...(mode === "dark"
            ? {
                primary: {
                  main: "#ffb300",
                  light: "#ffe54c",
                  dark: "#c68400",
                },
                warning: {
                  main: "#ffa726",
                },
                success: {
                  main: "#66bb6a",
                },
                error: {
                  main: "#ef5350",
                },
                background: {
                  default: "#0a0e14",
                  paper: "#111822",
                },
                divider: "rgba(255, 255, 255, 0.08)",
                text: {
                  primary: "#e6e6e6",
                  secondary: "#8c8c8c",
                },
              }
            : {
                primary: {
                  main: "#c68400",
                  light: "#ffb300",
                  dark: "#8c5d00",
                },
                warning: {
                  main: "#e65100",
                },
                background: {
                  default: "#f5f5f5",
                  paper: "#ffffff",
                },
              }),
        },
        typography: {
          fontFamily: [
            "Inter",
            "-apple-system",
            "BlinkMacSystemFont",
            '"Segoe UI"',
            "Roboto",
            "sans-serif",
          ].join(","),
        },
        shape: {
          borderRadius: 8,
        },
        components: {
          MuiCard: {
            defaultProps: {
              elevation: 0,
            },
          },
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: "none",
                fontWeight: 600,
              },
            },
          },
          MuiTextField: {
            defaultProps: {
              size: "small",
            },
          },
          MuiTableCell: {
            styleOverrides: {
              root: {
                borderBottomColor: "rgba(255, 255, 255, 0.06)",
              },
            },
          },
        },
      }),
    [mode]
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/securities" element={<Securities />} />
            <Route path="/securities/:id" element={<Securities />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/notifications" element={<Notifications />} />
          </Route>
        </Route>
      </Routes>
    </ThemeProvider>
  );
}

export default App;
