import { useEffect,useState } from 'react';
import PageHeader from '../../components/common/PageHeader.jsx';
import AlertList from '../../components/admin/AlertList.jsx';
import Loader from '../../components/common/Loader.jsx';
import ErrorState from '../../components/common/ErrorState.jsx';
import { getAlerts } from '../../services/adminService.js';
export default function Alerts(){const [items,setItems]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('');async function load(){setLoading(true);setError('');try{const d=await getAlerts();setItems(Array.isArray(d)?d:d.items||d.alerts||[]);}catch(e){setError(e.userMessage||e.message||'Could not load alerts.');}finally{setLoading(false);}}useEffect(()=>{load();},[]);return <><PageHeader eyebrow="OPERATIONS" title="Alerts" description="Database, model, resource, and repeated security event alerts returned by the backend."/>{loading?<Loader/>:error?<ErrorState message={error} onRetry={load}/>:<section className="panel"><AlertList items={items}/></section>}</>;}
