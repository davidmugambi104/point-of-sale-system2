import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import {
  Box,
  Button,
  TextField,
  Typography,
  Zoom,
  useTheme,
  Divider,
  IconButton,
  InputAdornment,
  FormControlLabel,
  Checkbox,
  FormHelperText
} from '@mui/material';
import { Person, Email, Lock, Visibility, VisibilityOff } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNotification } from '../context/NotificationContext';
import ParticlesBackground from '../components/ParticlesBackground';
import api from '../services/api';

const Signup = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { showNotification } = useNotification();
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverErrors, setServerErrors] = useState({});

  const formik = useFormik({
    initialValues: {
      username: '',
      email: '',
      password: '',
      role: 'cashier',
      agreeTerms: false
    },
    validationSchema: Yup.object({
      username: Yup.string()
        .min(3, 'Username must be at least 3 characters')
        .max(20, 'Username must be 20 characters or less')
        .required('Username is required')
        .matches(/^[a-zA-Z0-9_]+$/, 'No special characters except underscores'),
      email: Yup.string()
        .email('Invalid email address')
        .required('Email is required'),
      password: Yup.string()
        .min(8, 'Password must be at least 8 characters')
        .matches(
          /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
          'Must contain uppercase, number, and special character'
        )
        .required('Password is required'),
      role: Yup.string()
        .oneOf(['cashier', 'manager'], 'Invalid role')
        .required('Role is required'),
      agreeTerms: Yup.boolean()
        .oneOf([true], 'You must accept the terms and conditions')
        .required('Required')
    }),
    onSubmit: async (values, { setSubmitting, resetForm }) => {
      try {
        setIsSubmitting(true);
        setServerErrors({});
        
        const response = await api.post('/auth/signup', values);
        
        if (response.status === 201) {
          showNotification('Account created successfully! Please log in.', 'success');
          resetForm();
          navigate('/login', {
            state: { fromSignup: true },
            replace: true
          });
        }
      } catch (error) {
        if (error.response?.data?.errors) {
          setServerErrors(error.response.data.errors);
        } else {
          showNotification(
            error.response?.data?.message || 'Registration failed. Please try again.',
            'error'
          );
        }
      } finally {
        setIsSubmitting(false);
        setSubmitting(false);
      }
    }
  });

  useEffect(() => {
    if (Object.keys(serverErrors).length > 0) {
      Object.entries(serverErrors).forEach(([field, message]) => {
        formik.setFieldError(field, message);
      });
    }
  }, [serverErrors]);

  return (
    <Box sx={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
      background: 'linear-gradient(135deg, #4a148c 0%, #880e4f 100%)',
    }}>
      <ParticlesBackground particleColor="#ffffff" />
      
      <Zoom in={true} style={{ transitionDelay: '300ms' }}>
        <Box 
          component={motion.div}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          sx={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderRadius: 4,
            boxShadow: 24,
            p: { xs: 3, sm: 6 },
            width: { xs: '90%', sm: '450px' },
            zIndex: 1,
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Person sx={{ 
              fontSize: 48, 
              color: theme.palette.secondary.main,
              filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))'
            }} />
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700,
                background: `linear-gradient(45deg, ${theme.palette.secondary.main} 30%, ${theme.palette.primary.main} 90%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mt: 1,
                fontSize: { xs: '1.8rem', sm: '2.125rem' }
              }}
            >
              Create Account
            </Typography>
          </Box>

          <form onSubmit={formik.handleSubmit} noValidate>
            <TextField
              fullWidth
              id="username"
              name="username"
              label="Username"
              variant="outlined"
              margin="normal"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Person color="action" />
                  </InputAdornment>
                ),
                'aria-label': 'Username input',
              }}
              value={formik.values.username}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.username && Boolean(formik.errors.username)}
              helperText={formik.touched.username && formik.errors.username}
              disabled={isSubmitting}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }
              }}
            />

            <TextField
              fullWidth
              id="email"
              name="email"
              type="email"
              label="Email"
              variant="outlined"
              margin="normal"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Email color="action" />
                  </InputAdornment>
                ),
                'aria-label': 'Email input',
              }}
              value={formik.values.email}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.email && Boolean(formik.errors.email)}
              helperText={formik.touched.email && formik.errors.email}
              disabled={isSubmitting}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }
              }}
            />

            <TextField
              fullWidth
              id="password"
              name="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              variant="outlined"
              margin="normal"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Lock color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
                'aria-label': 'Password input',
              }}
              value={formik.values.password}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.password && Boolean(formik.errors.password)}
              helperText={formik.touched.password && formik.errors.password}
              disabled={isSubmitting}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }
              }}
            />

            <TextField
              fullWidth
              select
              id="role"
              name="role"
              label="Role"
              variant="outlined"
              margin="normal"
              SelectProps={{
                native: true,
                'aria-label': 'Select role',
              }}
              value={formik.values.role}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.role && Boolean(formik.errors.role)}
              helperText={formik.touched.role && formik.errors.role}
              disabled={isSubmitting}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }
              }}
            >
              <option value="cashier">Cashier</option>
              <option value="manager">Manager</option>
            </TextField>

            <FormControlLabel
              control={
                <Checkbox
                  name="agreeTerms"
                  color="primary"
                  checked={formik.values.agreeTerms}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  disabled={isSubmitting}
                />
              }
              label={
                <Typography variant="body2">
                  I agree to the{' '}
                  <Button 
                    component="a" 
                    href="/terms" 
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ p: 0, minWidth: 'auto' }}
                  >
                    Terms of Service
                  </Button>{' '}
                  and{' '}
                  <Button 
                    component="a" 
                    href="/privacy" 
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ p: 0, minWidth: 'auto' }}
                  >
                    Privacy Policy
                  </Button>
                </Typography>
              }
              sx={{ mt: 2, alignItems: 'flex-start' }}
            />
            {formik.touched.agreeTerms && formik.errors.agreeTerms && (
              <FormHelperText error sx={{ mt: 0, mb: 2 }}>
                {formik.errors.agreeTerms}
              </FormHelperText>
            )}

            <Button
              fullWidth
              variant="contained"
              type="submit"
              disabled={isSubmitting || !formik.isValid}
              sx={{
                mt: 3,
                mb: 2,
                py: 1.5,
                borderRadius: 2,
                fontSize: 16,
                fontWeight: 600,
                background: `linear-gradient(45deg, ${theme.palette.secondary.main} 30%, ${theme.palette.primary.main} 90%)`,
                '&:hover': {
                  transform: 'translateY(-1px)',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
                  background: `linear-gradient(45deg, ${theme.palette.secondary.dark} 30%, ${theme.palette.primary.dark} 90%)`,
                },
                transition: 'all 0.3s ease',
                opacity: isSubmitting ? 0.7 : 1
              }}
            >
              {isSubmitting ? 'Creating Account...' : 'Sign Up'}
            </Button>

            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Already Registered?
              </Typography>
            </Divider>

            <Box sx={{ textAlign: 'center' }}>
              <Button 
                onClick={() => navigate('/login')}
                sx={{
                  textTransform: 'none',
                  color: theme.palette.text.secondary,
                  '&:hover': {
                    color: theme.palette.secondary.main,
                    backgroundColor: 'transparent'
                  }
                }}
              >
                Already have an account? Sign In
              </Button>
            </Box>
          </form>
        </Box>
      </Zoom>
    </Box>
  );
};

export default Signup;