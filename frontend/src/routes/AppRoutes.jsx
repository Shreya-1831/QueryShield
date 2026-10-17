import { Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute.jsx';
import AdminRoute from './AdminRoute.jsx';
import AppLayout from '../layouts/AppLayout.jsx';
import AdminLayout from '../layouts/AdminLayout.jsx';
import AccessPage from '../pages/auth/AccessPage.jsx';
import DatabaseAccessPage from '../pages/auth/DatabaseAccessPage.jsx';
import AccessDenied from '../pages/auth/AccessDenied.jsx';
import EmployeeDashboard from '../pages/employee/EmployeeDashboard.jsx';
import QueryWorkspace from '../pages/employee/QueryWorkspace.jsx';
import QueryHistory from '../pages/employee/QueryHistory.jsx';
import Profile from '../pages/employee/Profile.jsx';
import AdminDashboard from '../pages/admin/AdminDashboard.jsx';
import UserManagement from '../pages/admin/UserManagement.jsx';
import Permissions from '../pages/admin/Permissions.jsx';
import AuditLogs from '../pages/admin/AuditLogs.jsx';
import SecurityEvents from '../pages/admin/SecurityEvents.jsx';
import SystemHealth from '../pages/admin/SystemHealth.jsx';
import ModelManagement from '../pages/admin/ModelManagement.jsx';
import Alerts from '../pages/admin/Alerts.jsx';
export const AppRoutes = [
  {path:'/access',element:<AccessPage/>},
  {path:'/database-access',element:<DatabaseAccessPage/>},
  {path:'/access-denied',element:<AccessDenied/>},
  {element:<ProtectedRoute/>,children:[{element:<AppLayout/>,children:[
    {path:'/app/dashboard',element:<EmployeeDashboard/>},
    {path:'/app/query',element:<QueryWorkspace/>},
    {path:'/app/history',element:<QueryHistory/>},
    {path:'/app/profile',element:<Profile/>},
  ]}]},
  {element:<AdminRoute/>,children:[{element:<AdminLayout/>,children:[
    {path:'/admin',element:<AdminDashboard/>},
    {path:'/admin/users',element:<UserManagement/>},
    {path:'/admin/permissions',element:<Permissions/>},
    {path:'/admin/audit-logs',element:<AuditLogs/>},
    {path:'/admin/security-events',element:<SecurityEvents/>},
    {path:'/admin/health',element:<SystemHealth/>},
    {path:'/admin/models',element:<ModelManagement/>},
    {path:'/admin/alerts',element:<Alerts/>},
  ]}]}
];
