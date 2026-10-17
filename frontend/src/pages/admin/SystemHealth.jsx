import PageHeader from '../../components/common/PageHeader.jsx';
import useHealth from '../../hooks/useHealth.js';
import HealthOverview from '../../components/admin/HealthOverview.jsx';
import ServiceStatus from '../../components/admin/ServiceStatus.jsx';
import ErrorState from '../../components/common/ErrorState.jsx';
export default function SystemHealth(){const h=useHealth();return <><PageHeader eyebrow="OPERATIONS" title="System health" description="Health data comes from the local FastAPI health endpoints." actions={<button className="button button-secondary" onClick={h.refresh}>Refresh</button>}/>{h.error&&<ErrorState message={h.error} onRetry={h.refresh}/>}<HealthOverview api={h.api} database={h.database}/><section className="panel"><h3>Services</h3><ServiceStatus name="FastAPI" status={h.api?.status||'unknown'} detail="Application API"/><ServiceStatus name="MySQL" status={h.database?.status||'unknown'} detail="Database connectivity"/><ServiceStatus name="Ollama" status={h.api?.ollama?.status||h.api?.services?.ollama||'Check backend health payload'} detail="Local model runtime"/></section></>;}
