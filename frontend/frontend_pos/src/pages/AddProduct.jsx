import { useState } from 'react';
import { TextField, Button, Container, Typography } from '@mui/material';
import { Formik, Form, Field } from 'formik';
import * as Yup from 'yup';
import api from '../services/api';

const validationSchema = Yup.object().shape({
  name: Yup.string().required('Required'),
  price: Yup.number().required('Required').min(0),
  stock: Yup.number().required('Required').min(0),
  category_id: Yup.number()
});

export default function AddProduct() {
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (values, { resetForm }) => {
    try {
      await api.post('/products', values);
      resetForm();
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Error adding product:', error);
    }
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" gutterBottom>Add New Product</Typography>
      
      <Formik
        initialValues={{ name: '', price: 0, stock: 0, category_id: '' }}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ errors, touched }) => (
          <Form>
            <Field
              as={TextField}
              name="name"
              label="Product Name"
              fullWidth
              margin="normal"
              error={touched.name && !!errors.name}
              helperText={touched.name && errors.name}
            />
            
            <Field
              as={TextField}
              name="price"
              label="Price"
              type="number"
              fullWidth
              margin="normal"
              error={touched.price && !!errors.price}
              helperText={touched.price && errors.price}
            />
            
            <Field
              as={TextField}
              name="stock"
              label="Stock Quantity"
              type="number"
              fullWidth
              margin="normal"
              error={touched.stock && !!errors.stock}
              helperText={touched.stock && errors.stock}
            />
            
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              sx={{ mt: 3 }}
            >
              Add Product
            </Button>
            
            {success && (
              <Typography color="success.main" sx={{ mt: 2 }}>
                Product added successfully!
              </Typography>
            )}
          </Form>
        )}
      </Formik>
    </Container>
  );
}