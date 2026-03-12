import { Box, Typography, Card, CardContent } from "@mui/material";
import { Notifications as NotificationsIcon } from "@mui/icons-material";

export default function Notifications() {
  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Notifications
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Stay updated on your trades and alerts
        </Typography>
      </Box>

      <Card
        sx={{
          borderRadius: 2,
          border: "1px solid",
          borderColor: "divider",
          minHeight: 400,
        }}
      >
        <CardContent
          sx={{
            p: 4,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: 400,
          }}
        >
          <NotificationsIcon
            sx={{ fontSize: 64, color: "text.disabled", mb: 2 }}
          />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Notifications
          </Typography>
          <Typography
            variant="body2"
            color="text.disabled"
            textAlign="center"
            maxWidth={400}
          >
            You will receive notifications about order executions, price alerts,
            and prediction signals here.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
