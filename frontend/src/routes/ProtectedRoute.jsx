import { Navigate, Outlet, useLocation } from 'react-router-dom';
import useAuth from '../hooks/useAuth.js';
import Loader from '../components/common/Loader.jsx';
export default function ProtectedRoute() {
  const {status} = useAuth(); const location = useLocation();
  if (status === 'checking') return <Loader full label="Checking verified identity…"/>;
  if (status !== 'authenticated') return <Navigate to="/access" replace state={{from:location.pathname}}/>;
  return <Outlet/>;
}
