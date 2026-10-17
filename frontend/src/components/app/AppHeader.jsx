import { Link } from 'react-router-dom';
import { Bell, ShieldCheck } from 'lucide-react';
import ThemeToggle from '../common/ThemeToggle.jsx';
import UserMenu from './UserMenu.jsx';
import useAuth from '../../hooks/useAuth.js';
export default function AppHeader({admin=false}){const {user,status}=useAuth();return <header className="app-header"><div><p className="eyebrow">{admin?'ADMIN CONSOLE':'SECURE WORKSPACE'}</p><strong>{admin?'System administration':'Your data workspace'}</strong></div><div className="header-actions"><span className={`connection-pill ${status==='authenticated'?'connected':''}`}><ShieldCheck size={15}/>{status==='authenticated'?'Identity verified':'Identity status'}</span><ThemeToggle/><UserMenu user={user}/></div></header>;}
