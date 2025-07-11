import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import DatePicker from 'react-datepicker';
import { Box, Typography, Paper } from '@mui/material';
import api from '../services/api';

export default function SalesReport() {
  const [reportData, setReportData] = useState([]);
  const [startDate, setStartDate] = useState(new Date(Date.now() - 7 * 86400000));
  const [endDate, setEndDate] = useState(new Date());

  const fetchReport = async () => {
    try {
      const { data } = await api.get('/reports/sales', {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      });
      setReportData(data.report);
    } catch (error) {
      console.error('Error fetching sales report:', error);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Sales Report</Typography>
      
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <DatePicker
          label="Start Date"
          value={startDate}
          onChange={(date) => setStartDate(date)}
        />
        <DatePicker
          label="End Date"
          value={endDate}
          onChange={(date) => setEndDate(date)}
        />
        <Button variant="contained" onClick={fetchReport}>
          Generate Report
        </Button>
      </Box>

      <LineChart width={800} height={400} data={reportData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="total_sales" stroke="#8884d8" />
        <Line type="monotone" dataKey="transaction_count" stroke="#82ca9d" />
      </LineChart>
    </Paper>
  );
}