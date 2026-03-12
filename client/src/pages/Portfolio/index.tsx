import { Box, Typography, Card, CardContent, Grid2 } from "@mui/material";
import { AccountBalance as PortfolioIcon } from "@mui/icons-material";

export default function Portfolio() {
  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Portfolio
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Track your holdings and performance
        </Typography>
      </Box>

      {/* Summary Cards */}
      <Grid2 container spacing={3} sx={{ mb: 3 }}>
        {[
          { label: "Total Value", value: "$0.00" },
          { label: "Cash Balance", value: "$0.00" },
          { label: "Total P&L", value: "$0.00" },
          { label: "Holdings", value: "0" },
        ].map((item) => (
          <Grid2 size={{ xs: 6, md: 3 }} key={item.label}>
            <Card
              sx={{
                borderRadius: 2,
                border: "1px solid",
                borderColor: "divider",
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Typography variant="body2" color="text.secondary">
                  {item.label}
                </Typography>
                <Typography variant="h6" fontWeight={700} sx={{ mt: 0.5 }}>
                  {item.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid2>
        ))}
      </Grid2>

      {/* Holdings */}
      <Card
        sx={{
          borderRadius: 2,
          border: "1px solid",
          borderColor: "divider",
          minHeight: 300,
        }}
      >
        <CardContent
          sx={{
            p: 4,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: 300,
          }}
        >
          <PortfolioIcon sx={{ fontSize: 64, color: "text.disabled", mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Holdings
          </Typography>
          <Typography
            variant="body2"
            color="text.disabled"
            textAlign="center"
            maxWidth={400}
          >
            Your portfolio holdings will appear here once you start trading.
            Navigate to the Trading page to place your first order.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
