import { useEffect, useState } from 'react';
import PageHeader from '../../components/common/PageHeader.jsx';
import DataTable from '../../components/app/DataTable.jsx';
import Loader from '../../components/common/Loader.jsx';
import ErrorState from '../../components/common/ErrorState.jsx';
import { getQueryHistory } from '../../services/historyService.js';
import { formatDate } from '../../utils/formatters.js';
export default function QueryHistory(){const [items,setItems]=useState([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('');async function load(){setLoading(true);setError('');try{setItems(await getQueryHistory());}catch(e){setError(e.userMessage||e.message||'History endpoint is not available.');}finally{setLoading(false);}}useEffect(()=>{load();},[]);return <><PageHeader eyebrow="CONVERSATIONS" title="Query history" description="History depends on the authorized history endpoint configured in FastAPI."/>{loading?<Loader label="Loading query history…"/>:error?<ErrorState message={error} onRetry={load}/>:<DataTable rows={items} columns={[{key:'created_at',label:'Time',render:formatDate},{key:'prompt',label:'Question'},{key:'status',label:'Status'},{key:'row_count',label:'Rows'}]}/>}</>;}
