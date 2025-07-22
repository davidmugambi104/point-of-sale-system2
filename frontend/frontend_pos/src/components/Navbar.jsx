import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button, AppBar, Toolbar, Typography } from '@mui/material';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          VIETECH
        </Typography>
        {isAuthenticated() ? (
          <>
            <Typography variant="subtitle1" sx={{ mr: 2 }}>
              Welcome, {user.name}
            </Typography>
            <Button color="inherit" onClick={logout}>
              Logout
            </Button>
          </>
        ) : (
          <Button color="inherit" component={Link} to="/login">
            Login
          </Button>
        )}
      </Toolbar>
    </AppBar>
  );
}