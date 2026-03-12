import { Box, Typography, Card, CardContent, Grid2 } from "@mui/material";
import { SwapHoriz as TradingIcon } from "@mui/icons-material";

export default function Trading() {
  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Trading
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Place orders and manage your trades
        </Typography>
      </Box>

      <Grid2 container spacing={3}>
        {/* Order Form Placeholder */}
        <Grid2 size={{ xs: 12, md: 4 }}>
          <Card
            sx={{
              borderRadius: 2,
              border: "1px solid",
              borderColor: "divider",
              minHeight: 500,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
                New Order
              </Typography>
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  minHeight: 400,
                }}
              >
                <TradingIcon
                  sx={{ fontSize: 48, color: "text.disabled", mb: 2 }}
                />
                <Typography
                  variant="body2"
                  color="text.secondary"
                  textAlign="center"
                >
                  Order placement form will be available here
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid2>

        {/* Open Orders */}
        <Grid2 size={{ xs: 12, md: 8 }}>
          <Card
            sx={{
              borderRadius: 2,
              border: "1px solid",
              borderColor: "divider",
              minHeight: 500,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
                Open Orders
              </Typography>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  minHeight: 400,
                  color: "text.secondary",
                }}
              >
                <Typography variant="body1">No open orders</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>
    </Box>
  );
}
