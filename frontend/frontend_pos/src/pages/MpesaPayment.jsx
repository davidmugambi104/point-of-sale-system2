import { useState } from 'react';
import { TextField, Button, Container, Typography } from '@mui/material';
import api from '../services/api';

export default function MpesaPayment() {
  const [paymentData, setPaymentData] = useState({
    phone: '',
    amount: '',
    transactionId: ''
  });
  const [status, setStatus] = useState('');

  const handlePayment = async () => {
    try {
      await api.post('/payments/mpesa', paymentData);
      setStatus('Payment initiated successfully! Check your phone to complete');
    } catch (error) {
      setStatus('Payment failed. Please try again.');
      console.error('MPesa payment error:', error);
    }
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" gutterBottom>MPesa Payment</Typography>
      
      <TextField
        label="Phone Number"
        fullWidth
        margin="normal"
        value={paymentData.phone}
        onChange={(e) => setPaymentData({ ...paymentData, phone: e.target.value })}
      />
      
      <TextField
        label="Amount"
        type="number"
        fullWidth
        margin="normal"
        value={paymentData.amount}
        onChange={(e) => setPaymentData({ ...paymentData, amount: e.target.value })}
      />
      
      <TextField
        label="Transaction ID"
        fullWidth
        margin="normal"
        value={paymentData.transactionId}
        onChange={(e) => setPaymentData({ ...paymentData, transactionId: e.target.value })}
      />
      
      <Button
        variant="contained"
        color="primary"
        fullWidth
        onClick={handlePayment}
        sx={{ mt: 2 }}
      >
        Process Payment
      </Button>
      
      {status && (
        <Typography color={status.includes('success') ? 'success.main' : 'error.main'} sx={{ mt: 2 }}>
          {status}
        </Typography>
      )}
    </Container>
  );
}