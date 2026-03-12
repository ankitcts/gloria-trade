import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from "@mui/material";
import { Search as SearchIcon } from "@mui/icons-material";

const PLACEHOLDER_SECURITIES = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    sector: "Technology",
    price: "--",
    change: "--",
  },
  {
    symbol: "GOOGL",
    name: "Alphabet Inc.",
    sector: "Technology",
    price: "--",
    change: "--",
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corp.",
    sector: "Technology",
    price: "--",
    change: "--",
  },
];

export default function Securities() {
  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Securities
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Browse and search available securities
          </Typography>
        </Box>
      </Box>

      {/* Search */}
      <TextField
        fullWidth
        placeholder="Search securities by name or symbol..."
        variant="outlined"
        sx={{ mb: 3 }}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          },
        }}
      />

      {/* Table */}
      <Card
        sx={{
          borderRadius: 2,
          border: "1px solid",
          borderColor: "divider",
        }}
      >
        <CardContent sx={{ p: 0 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>Symbol</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Sector</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="right">
                    Price
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="right">
                    Change
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {PLACEHOLDER_SECURITIES.map((sec) => (
                  <TableRow
                    key={sec.symbol}
                    hover
                    sx={{ cursor: "pointer" }}
                  >
                    <TableCell>
                      <Chip
                        label={sec.symbol}
                        size="small"
                        sx={{
                          fontWeight: 700,
                          bgcolor: "rgba(255, 179, 0, 0.12)",
                          color: "warning.main",
                        }}
                      />
                    </TableCell>
                    <TableCell>{sec.name}</TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {sec.sector}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{sec.price}</TableCell>
                    <TableCell align="right">{sec.change}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}
