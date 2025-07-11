import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, CircularProgress, Typography, Button, Box, FormControl, InputLabel, Input } from '@mui/material';
import axios from 'axios';

export default function ProductList() {
  const [allProducts, setAllProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [newProduct, setNewProduct] = useState({
    name: '',
    price: '',
    stock: '',
    category_id: ''
  });

  // Reusable fetch function
// Updated fetchProducts function
const fetchProducts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      // Check if token exists
      if (!token) {
        setError('Authentication required. Please login.');
        return;
      }
  
      const { data } = await axios.get('http://127.0.0.1:5000/products', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      setAllProducts(data.products);
      setFilteredProducts(data.products);
      setError('');
    } catch (error) {
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error ||
                          error.message || 
                          'Failed to fetch products';
      setError(errorMessage);
      
      // Handle 401 Unauthorized
      if (error.response?.status === 401) {
        // Redirect to login or refresh token
        localStorage.removeItem('access_token');
      }
    } finally {
      setLoading(false);
    }
  };

  // Fetch products on mount
  useEffect(() => {
    fetchProducts();
  }, []);

  // Client-side filtering
  useEffect(() => {
    const filtered = allProducts.filter(product =>
      product.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredProducts(filtered);
  }, [searchTerm, allProducts]);

  // Add new product
  const handleAddProduct = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:5000/products', newProduct, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      // Refresh product list after successful addition
      await fetchProducts();
      // Reset form
      setNewProduct({
        name: '',
        price: '',
        stock: '',
        category_id: ''
      });
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to add product');
    }
  };

  return (
    <div>
      {/* Search Input */}
      <TextField
        label="Search Products"
        variant="outlined"
        fullWidth
        margin="normal"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      {/* Add Product Form */}
      <Box component="form" onSubmit={handleAddProduct} sx={{ mb: 4, p: 2, border: '1px solid #ddd', borderRadius: 1 }}>
        <Typography variant="h6" gutterBottom>Add New Product</Typography>
        <FormControl fullWidth margin="normal">
          <InputLabel>Product Name</InputLabel>
          <Input
            value={newProduct.name}
            onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
            required
          />
        </FormControl>
        
        <FormControl fullWidth margin="normal">
          <InputLabel>Price</InputLabel>
          <Input
            type="number"
            value={newProduct.price}
            onChange={(e) => setNewProduct({ ...newProduct, price: e.target.value })}
            required
          />
        </FormControl>

        <FormControl fullWidth margin="normal">
          <InputLabel>Stock Quantity</InputLabel>
          <Input
            type="number"
            value={newProduct.stock}
            onChange={(e) => setNewProduct({ ...newProduct, stock: e.target.value })}
            required
          />
        </FormControl>

        <FormControl fullWidth margin="normal">
          <InputLabel>Category ID (optional)</InputLabel>
          <Input
            value={newProduct.category_id}
            onChange={(e) => setNewProduct({ ...newProduct, category_id: e.target.value })}
          />
        </FormControl>

        <Button type="submit" variant="contained" sx={{ mt: 2 }}>
          Add Product
        </Button>
      </Box>

      {/* Loading and Error States */}
      {loading && <CircularProgress style={{ margin: '20px auto', display: 'block' }} />}
      
      {error && (
        <Typography color="error" align="center" style={{ margin: '20px 0' }}>
          {error}
        </Typography>
      )}

      {/* Products Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Price</TableCell>
              <TableCell>Stock</TableCell>
              <TableCell>Category ID</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredProducts.length > 0 ? (
              filteredProducts.map((product) => (
                <TableRow key={product.id}>
                  <TableCell>{product.name}</TableCell>
                  <TableCell>${product.price}</TableCell>
                  <TableCell>{product.stock}</TableCell>
                  <TableCell>{product.category_id || '-'}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  {!loading && 'No products found'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}