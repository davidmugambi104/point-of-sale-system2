import { BrowserRouter as Router } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import AppRoutes from './routes';
import { Container } from '@mui/material';
import { NotificationProvider } from './context/NotificationContext';

export default function App() {
  return (
    <NotificationProvider>
   <AuthProvider>
    <Router>

        <Navbar />
        <Container maxWidth="xl" sx={{ mt: 4 }}>
          <AppRoutes />
        </Container>
    </Router>
    </AuthProvider>
    </NotificationProvider>
  );
}