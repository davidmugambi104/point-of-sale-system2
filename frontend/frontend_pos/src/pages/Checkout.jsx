import { useContext, useState } from 'react';
import { CartContext } from '../context/CartContext';
import { Button, List, ListItem, ListItemText, Typography } from '@mui/material';
import axios from 'axios';

export default function Checkout() {
  const { cart, total, clearCart } = useContext(CartContext);
  const [paymentStatus, setPaymentStatus] = useState('');

  const handleCheckout = async () => {
    try {
      await axios.post('/checkout', { items: cart });
      clearCart();
      setPaymentStatus('Checkout successful!');
    } catch (error) {
      setPaymentStatus('Checkout failed. Please try again.');
      console.error('Checkout error:', error);
    }
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>Checkout</Typography>
      
      <List>
        {cart.map(item => (
          <ListItem key={item.id}>
            <ListItemText
              primary={item.name}
              secondary={`Quantity: ${item.quantity} - $${item.price * item.quantity}`}
            />
          </ListItem>
        ))}
      </List>

      <Typography variant="h6">Total: ${total}</Typography>
      
      <Button
        variant="contained"
        color="primary"
        onClick={handleCheckout}
        disabled={cart.length === 0}
        sx={{ mt: 2 }}
      >
        Complete Checkout
      </Button>

      {paymentStatus && (
        <Typography color={paymentStatus.includes('success') ? 'success.main' : 'error.main'} sx={{ mt: 2 }}>
          {paymentStatus}
        </Typography>
      )}
    </div>
  );
}