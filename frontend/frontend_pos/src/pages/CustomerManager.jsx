import { useState, useEffect } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import { Button, Dialog, DialogTitle, DialogContent, TextField } from '@mui/material';
import api from '../services/api';

const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'name', headerName: 'Name', width: 200 },
  { field: 'email', headerName: 'Email', width: 250 },
  { field: 'phone', headerName: 'Phone', width: 150 },
  { field: 'loyalty_points', headerName: 'Loyalty Points', width: 130 }
];

export default function CustomerManager() {
  const [customers, setCustomers] = useState([]);
  const [open, setOpen] = useState(false);
  const [newCustomer, setNewCustomer] = useState({ name: '', email: '', phone: '' });

  const fetchCustomers = async () => {
    try {
      const { data } = await api.get('/customers');
      setCustomers(data.customers);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  const handleAddCustomer = async () => {
    try {
      await api.post('/addcustomer', newCustomer);
      fetchCustomers();
      setOpen(false);
      setNewCustomer({ name: '', email: '', phone: '' });
    } catch (error) {
      console.error('Error adding customer:', error);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  return (
    <div style={{ height: 600, width: '100%' }}>
      <Button variant="contained" onClick={() => setOpen(true)} sx={{ mb: 2 }}>
        Add New Customer
      </Button>

      <DataGrid
        rows={customers}
        columns={columns}
        pageSize={10}
        rowsPerPageOptions={[10, 25, 50]}
      />

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>New Customer</DialogTitle>
        <DialogContent>
          <TextField
            label="Name"
            fullWidth
            margin="normal"
            value={newCustomer.name}
            onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
          />
          <TextField
            label="Email"
            fullWidth
            margin="normal"
            value={newCustomer.email}
            onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
          />
          <TextField
            label="Phone"
            fullWidth
            margin="normal"
            value={newCustomer.phone}
            onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
          />
          <Button
            variant="contained"
            onClick={handleAddCustomer}
            fullWidth
            sx={{ mt: 2 }}
          >
            Save Customer
          </Button>
        </DialogContent>
      </Dialog>
    </div>
  );
}