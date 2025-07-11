import { useState, useEffect } from 'react';
import { Grid, Alert, CircularProgress } from '@mui/material';
import InventoryChart from '../components/InventoryChart';
import api from '../services/api';

export default function Inventory() {
  const [inventoryData, setInventoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchInventory = async () => {
      try {
        const { data } = await api.get('/inventory-monitoring');
        setInventoryData(data);
      } catch (err) {
        setError('Failed to load inventory data');
      } finally {
        setLoading(false);
      }
    };
    fetchInventory();
  }, []);

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <InventoryChart data={inventoryData} />
      </Grid>
      <Grid item xs={12} md={6}>
        <h3>Critical Stock Items</h3>
        {inventoryData.critical_items.map(item => (
          <Alert key={item.id} severity="warning">
            {item.name} - {item.stock_level} remaining
          </Alert>
        ))}
      </Grid>
    </Grid>
  );
}