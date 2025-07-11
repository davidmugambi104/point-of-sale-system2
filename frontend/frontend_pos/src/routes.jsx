import { Routes, Route } from 'react-router-dom';
import PrivateRoute from './components/PrivateRoute';
import AdminRoute from './components/AdminRoute';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ProductList from './pages/ProductList';
import AddProduct from './pages/AddProduct';
import Inventory from './pages/Inventory';
import Checkout from './pages/Checkout';
import SalesReport from './pages/SalesReport';
import CustomerManager from './pages/CustomerManager';
import AdminDashboard from './pages/AdminDashboard';
import AuditLogs from './pages/AuditLogs';
import MpesaPayment from './pages/MpesaPayment';
import ThreeDInterface from './pages/ThreeDInterface';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      
      {/* <Route element={<PrivateRoute />}> */}
        <Route path="/" element={<ProductList />} />
        <Route path="/products" element={<ProductList />} />
        <Route path="/products/add" element={<AddProduct />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/sales" element={<SalesReport />} />
        <Route path="/customers" element={<CustomerManager />} />
        <Route path="/payment/mpesa" element={<MpesaPayment />} />
        <Route path="/3d-interface" element={<ThreeDInterface />} />

        <Route element={<AdminRoute />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/audit-logs" element={<AuditLogs />} />
        </Route>
      {/* </Route> */}
    </Routes>
  );
}
// import { Routes, Route, Navigate } from 'react-router-dom';
// import { useAuth } from './AuthContext';
// import Login from './Login';
// import Dashboard from './Dashboard';
// import Home from './Home';

// function ProtectedRoute({ children }) {
//   const { isAuthenticated, loading } = useAuth();

//   if (loading) return <div>Loading...</div>;
//   return isAuthenticated() ? children : <Navigate to="/login" replace />;
// }

// export default function AppRoutes() {
//   return (
//     <Routes>
//       <Route path="/" element={<Home />} />
//       <Route path="/login" element={<Login />} />
//       <Route
//         path="/dashboard"
//         element={
//           <ProtectedRoute>
//             <Dashboard />
//           </ProtectedRoute>
//         }
//       />
//       <Route path="*" element={<Navigate to="/" replace />} />
//     </Routes>
//   );
// }