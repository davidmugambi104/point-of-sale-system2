import { useState, useEffect } from 'react';
import { Grid, Card, CardContent, Typography } from '@mui/material';
import api from '../services/api';

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    totalSales: 0,
    activeProducts: 0,
    criticalInventory: 0,
    recentCustomers: 0
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data } = await api.get('/admin/dashboard');
        setStats(data);
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
      }
    };
    fetchStats();
  }, []);

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Total Sales</Typography>
            <Typography variant="h4">${stats.totalSales}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Active Products</Typography>
            <Typography variant="h4">{stats.activeProducts}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Critical Inventory</Typography>
            <Typography variant="h4">{stats.criticalInventory}</Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">New Customers</Typography>
            <Typography variant="h4">{stats.recentCustomers}</Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}