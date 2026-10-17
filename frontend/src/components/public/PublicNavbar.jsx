import { Link, NavLink } from 'react-router-dom';
import { Menu, X, ArrowUpRight } from 'lucide-react';
import { useState } from 'react';
import Logo from '../common/Logo.jsx';
import ThemeToggle from '../common/ThemeToggle.jsx';
import { NAV_LINKS } from '../../utils/constants.js';
export default function PublicNavbar(){const [open,setOpen]=useState(false);return <header className="public-nav"><div className="container nav-inner"><Logo/><button className="icon-button mobile-menu-toggle" aria-label="Toggle navigation" onClick={()=>setOpen(v=>!v)}>{open?<X/>:<Menu/>}</button><nav className={`nav-links ${open?'nav-open':''}`}>{NAV_LINKS.map(x=><NavLink key={x.to} to={x.to} onClick={()=>setOpen(false)}>{x.label}</NavLink>)}<Link className="mobile-workspace-link" to="/access">Open Workspace <ArrowUpRight size={16}/></Link></nav><div className="nav-actions"><ThemeToggle/><Link className="button button-primary" to="/access">Open Workspace <ArrowUpRight size={16}/></Link></div></div></header>;}
