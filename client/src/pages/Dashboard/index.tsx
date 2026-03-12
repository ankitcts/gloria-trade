import { Box, Typography, Grid2, Card, CardContent } from "@mui/material";
import {
  TrendingUp as TrendingUpIcon,
  AccountBalance as AccountBalanceIcon,
  ShowChart as ShowChartIcon,
  Psychology as PredictionsIcon,
} from "@mui/icons-material";
import { useAuthStore } from "@/stores/authStore";

const SUMMARY_CARDS = [
  {
    title: "Portfolio Value",
    value: "$0.00",
    change: "+0.00%",
    icon: <AccountBalanceIcon />,
    color: "#ffb300",
  },
  {
    title: "Today's P&L",
    value: "$0.00",
    change: "0.00%",
    icon: <TrendingUpIcon />,
    color: "#66bb6a",
  },
  {
    title: "Open Positions",
    value: "0",
    change: "",
    icon: <ShowChartIcon />,
    color: "#42a5f5",
  },
  {
    title: "Active Predictions",
    value: "0",
    change: "",
    icon: <PredictionsIcon />,
    color: "#ab47bc",
  },
];

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);

  return (
    <Box>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Welcome back
          {user?.first_name ? `, ${user.first_name}` : ""}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
          Here is your trading overview for today
        </Typography>
      </Box>

      {/* Summary Cards */}
      <Grid2 container spacing={3} sx={{ mb: 4 }}>
        {SUMMARY_CARDS.map((card) => (
          <Grid2 size={{ xs: 12, sm: 6, lg: 3 }} key={card.title}>
            <Card
              sx={{
                borderRadius: 2,
                border: "1px solid",
                borderColor: "divider",
                transition: "border-color 0.2s",
                "&:hover": {
                  borderColor: card.color,
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    mb: 2,
                  }}
                >
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    fontWeight={500}
                  >
                    {card.title}
                  </Typography>
                  <Box
                    sx={{
                      color: card.color,
                      opacity: 0.8,
                    }}
                  >
                    {card.icon}
                  </Box>
                </Box>
                <Typography variant="h5" fontWeight={700}>
                  {card.value}
                </Typography>
                {card.change && (
                  <Typography
                    variant="body2"
                    sx={{
                      mt: 0.5,
                      color: card.change.startsWith("+")
                        ? "success.main"
                        : card.change.startsWith("-")
                          ? "error.main"
                          : "text.secondary",
                    }}
                  >
                    {card.change}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid2>
        ))}
      </Grid2>

      {/* Placeholder Charts Area */}
      <Grid2 container spacing={3}>
        <Grid2 size={{ xs: 12, lg: 8 }}>
          <Card
            sx={{
              borderRadius: 2,
              border: "1px solid",
              borderColor: "divider",
              minHeight: 400,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
                Portfolio Performance
              </Typography>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  minHeight: 320,
                  color: "text.secondary",
                }}
              >
                <Typography variant="body1">
                  Portfolio chart will appear here once you start trading
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid2>
        <Grid2 size={{ xs: 12, lg: 4 }}>
          <Card
            sx={{
              borderRadius: 2,
              border: "1px solid",
              borderColor: "divider",
              minHeight: 400,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
                Recent Activity
              </Typography>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  minHeight: 320,
                  color: "text.secondary",
                }}
              >
                <Typography variant="body1">No recent activity</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>
    </Box>
  );
}
