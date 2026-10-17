import { useEffect,useState } from 'react';
import PageHeader from '../../components/common/PageHeader.jsx';
import SecurityEventTable from '../../components/admin/SecurityEventTable.jsx';
import Loader from '../../components/common/Loader.jsx';
import ErrorState from '../../components/common/ErrorState.jsx';
import { getSecurityEvents } from '../../services/adminService.js';
export default function SecurityEvents(){const [rows,setRows]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('');async function load(){setLoading(true);setError('');try{const d=await getSecurityEvents();setRows(Array.isArray(d)?d:d.items||d.events||[]);}catch(e){setError(e.userMessage||e.message||'Could not load security events.');}finally{setLoading(false);}}useEffect(()=>{load();},[]);return <><PageHeader eyebrow="SECURITY" title="Security events" description="Review prompt-security and authorization events returned by the backend."/>{loading?<Loader/>:error?<ErrorState message={error} onRetry={load}/>:<SecurityEventTable rows={rows}/>}</>;}
