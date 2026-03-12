import { Box, CircularProgress } from "@mui/material";

interface LoadingSpinnerProps {
  size?: number;
  fullScreen?: boolean;
}

export default function LoadingSpinner({
  size = 48,
  fullScreen = false,
}: LoadingSpinnerProps) {
  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight={fullScreen ? "100vh" : "200px"}
      width="100%"
    >
      <CircularProgress size={size} sx={{ color: "primary.main" }} />
    </Box>
  );
}
