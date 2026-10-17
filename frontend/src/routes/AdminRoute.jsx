import { Navigate, Outlet } from 'react-router-dom';
import useAuth from '../hooks/useAuth.js';
import { isAdmin } from '../utils/permissions.js';
import Loader from '../components/common/Loader.jsx';
export default function AdminRoute() {
  const {user,status} = useAuth();
  if (status === 'checking') return <Loader full label="Verifying administrator access…"/>;
  if (status !== 'authenticated') return <Navigate to="/access" replace/>;
  if (!isAdmin(user)) return <Navigate to="/access-denied" replace/>;
  return <Outlet/>;
}
