import { Link } from 'react-router-dom';
import { UserRound } from 'lucide-react';
export default function UserMenu({user}){const label=user?.display_name||user?.name||user?.username||'Verified user';return <Link className="user-menu" to="/app/profile" title={label}><span className="avatar"><UserRound size={17}/></span><span className="user-menu-name">{label}</span></Link>;}
