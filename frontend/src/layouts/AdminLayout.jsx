import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/app/AppSidebar.jsx';
import AppHeader from '../components/app/AppHeader.jsx';
export default function AdminLayout(){return <div className="workspace-shell"><AppSidebar admin/><div className="workspace-main"><AppHeader admin/><main className="workspace-content"><Outlet/></main></div></div>;}
