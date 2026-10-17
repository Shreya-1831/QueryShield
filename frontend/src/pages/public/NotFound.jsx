import { Link } from 'react-router-dom';
import Container from '../../components/common/Container.jsx';
import { ShieldAlert } from 'lucide-react';
export default function NotFound(){return <section className="page-section"><Container className="state-card"><ShieldAlert size={36}/><p className="eyebrow">404 · NOT FOUND</p><h1>This page isn't in the perimeter.</h1><p>The page may have moved or the URL may be incorrect.</p><Link className="button button-primary" to="/">Return home</Link></Container></section>;}
