import { Outlet } from 'react-router-dom';
import AppSidebar from '../components/app/AppSidebar.jsx';
import AppHeader from '../components/app/AppHeader.jsx';
export default function AppLayout(){return <div className="workspace-shell"><AppSidebar/><div className="workspace-main"><AppHeader/><main className="workspace-content"><Outlet/></main></div></div>;}
