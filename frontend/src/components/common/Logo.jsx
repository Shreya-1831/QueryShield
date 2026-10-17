import { Link } from 'react-router-dom';
export default function Logo({to='/',small=false}) { return <Link to={to} className={`brand ${small?'brand-small':''}`} aria-label="QueryShield home"><img src="/logo.svg" alt="" /><span>QueryShield</span></Link>; }
