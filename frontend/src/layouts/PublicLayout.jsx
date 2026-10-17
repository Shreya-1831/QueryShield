import { Outlet } from 'react-router-dom';
import PublicNavbar from '../components/public/PublicNavbar.jsx';
import PublicFooter from '../components/public/PublicFooter.jsx';
export default function PublicLayout(){ return <div className="public-shell"><PublicNavbar/><main><Outlet/></main><PublicFooter/></div>; }
