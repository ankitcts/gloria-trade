import { Box, Typography, Card, CardContent, Grid2 } from "@mui/material";
import { Psychology as PredictionsIcon } from "@mui/icons-material";

export default function Predictions() {
  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Predictions
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          AI-powered market predictions and signals
        </Typography>
      </Box>

      <Grid2 container spacing={3}>
        <Grid2 size={12}>
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
              <PredictionsIcon
                sx={{ fontSize: 64, color: "text.disabled", mb: 2 }}
              />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No Predictions Available
              </Typography>
              <Typography
                variant="body2"
                color="text.disabled"
                textAlign="center"
                maxWidth={400}
              >
                AI predictions will appear here once the prediction models have
                processed market data. Check back soon for actionable trading
                signals.
              </Typography>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>
    </Box>
  );
}
