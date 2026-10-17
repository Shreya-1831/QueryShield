import { useEffect,useState } from 'react';
import PageHeader from '../../components/common/PageHeader.jsx';
import AuditTable from '../../components/admin/AuditTable.jsx';
import Loader from '../../components/common/Loader.jsx';
import ErrorState from '../../components/common/ErrorState.jsx';
import { getAuditLogs } from '../../services/adminService.js';
export default function AuditLogs(){const [rows,setRows]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('');async function load(){setLoading(true);setError('');try{const d=await getAuditLogs();setRows(Array.isArray(d)?d:d.items||d.logs||[]);}catch(e){setError(e.userMessage||e.message||'Could not load audit logs.');}finally{setLoading(false);}}useEffect(()=>{load();},[]);return <><PageHeader eyebrow="MONITORING" title="Audit logs" description="Audit data is sensitive; this page must remain Admin-only on the backend."/>{loading?<Loader/>:error?<ErrorState message={error} onRetry={load}/>:<AuditTable rows={rows}/>}</>;}
