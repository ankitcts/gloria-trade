import { useState } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Link,
  Alert,
  InputAdornment,
  IconButton,
} from "@mui/material";
import {
  Visibility,
  VisibilityOff,
  Email as EmailIcon,
} from "@mui/icons-material";
import { useLogin } from "@/api/hooks/useAuth";

export default function Login() {
  const navigate = useNavigate();
  const loginMutation = useLogin();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await loginMutation.mutateAsync({ email, password });
      navigate("/");
    } catch {
      // Error is handled by the mutation
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: (theme) =>
          theme.palette.mode === "dark"
            ? "linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%)"
            : "linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)",
        p: 2,
      }}
    >
      <Card
        sx={{
          maxWidth: 440,
          width: "100%",
          borderRadius: 3,
          border: "1px solid",
          borderColor: "divider",
        }}
      >
        <CardContent sx={{ p: 4 }}>
          {/* Logo */}
          <Box sx={{ textAlign: "center", mb: 4 }}>
            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: 2,
                background: (theme) =>
                  `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.warning.main})`,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 800,
                fontSize: "1.4rem",
                color: "#000",
                mb: 2,
              }}
            >
              GT
            </Box>
            <Typography variant="h5" fontWeight={700}>
              Welcome Back
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Sign in to your Gloria Trade account
            </Typography>
          </Box>

          {/* Error */}
          {loginMutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {loginMutation.error instanceof Error
                ? loginMutation.error.message
                : "Invalid email or password"}
            </Alert>
          )}

          {/* Form */}
          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              margin="normal"
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailIcon fontSize="small" />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <TextField
              fullWidth
              label="Password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              margin="normal"
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        size="small"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loginMutation.isPending}
              sx={{
                mt: 3,
                mb: 2,
                py: 1.5,
                fontWeight: 600,
                background: (theme) =>
                  `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.warning.main})`,
                color: "#000",
                "&:hover": {
                  background: (theme) =>
                    `linear-gradient(135deg, ${theme.palette.primary.dark}, ${theme.palette.warning.dark})`,
                },
              }}
            >
              {loginMutation.isPending ? "Signing in..." : "Sign In"}
            </Button>

            <Typography variant="body2" textAlign="center" color="text.secondary">
              Don&apos;t have an account?{" "}
              <Link component={RouterLink} to="/register" color="primary">
                Sign up
              </Link>
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
