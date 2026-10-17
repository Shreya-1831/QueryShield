import { Link } from 'react-router-dom';
import { ShieldX } from 'lucide-react';
export default function AccessDenied(){return <main className="centered-page"><div className="state-card"><ShieldX size={36}/><h1>Access restricted</h1><p>Your verified role does not permit this area. Contact your system administrator if you believe this is incorrect.</p><Link className="button button-primary" to="/app/dashboard">Go to workspace</Link></div></main>;}
