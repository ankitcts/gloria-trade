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
  Grid2,
} from "@mui/material";
import {
  Visibility,
  VisibilityOff,
  Email as EmailIcon,
  Person as PersonIcon,
} from "@mui/icons-material";
import { useRegister } from "@/api/hooks/useAuth";

export default function Register() {
  const navigate = useNavigate();
  const registerMutation = useRegister();

  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
    confirmPassword: "",
    first_name: "",
    last_name: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState("");

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
    setValidationError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setValidationError("Passwords do not match");
      return;
    }

    if (formData.password.length < 8) {
      setValidationError("Password must be at least 8 characters");
      return;
    }

    try {
      await registerMutation.mutateAsync({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
      });
      navigate("/login");
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
          maxWidth: 480,
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
              Create Account
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Join Gloria Trade and start investing
            </Typography>
          </Box>

          {/* Errors */}
          {(validationError || registerMutation.isError) && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {validationError ||
                (registerMutation.error instanceof Error
                  ? registerMutation.error.message
                  : "Registration failed")}
            </Alert>
          )}

          {/* Form */}
          <Box component="form" onSubmit={handleSubmit}>
            <Grid2 container spacing={2}>
              <Grid2 size={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={formData.first_name}
                  onChange={handleChange("first_name")}
                  required
                />
              </Grid2>
              <Grid2 size={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  value={formData.last_name}
                  onChange={handleChange("last_name")}
                  required
                />
              </Grid2>
            </Grid2>

            <TextField
              fullWidth
              label="Username"
              value={formData.username}
              onChange={handleChange("username")}
              required
              margin="normal"
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <PersonIcon fontSize="small" />
                    </InputAdornment>
                  ),
                },
              }}
            />

            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={handleChange("email")}
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
              value={formData.password}
              onChange={handleChange("password")}
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

            <TextField
              fullWidth
              label="Confirm Password"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange("confirmPassword")}
              required
              margin="normal"
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={registerMutation.isPending}
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
              {registerMutation.isPending ? "Creating account..." : "Sign Up"}
            </Button>

            <Typography variant="body2" textAlign="center" color="text.secondary">
              Already have an account?{" "}
              <Link component={RouterLink} to="/login" color="primary">
                Sign in
              </Link>
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
