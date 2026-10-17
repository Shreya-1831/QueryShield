import StatusBadge from '../app/StatusBadge.jsx';
export default function ServiceStatus({name,status,detail}){return <div className="service-row"><div><strong>{name}</strong>{detail&&<p>{detail}</p>}</div><StatusBadge status={status||'unknown'}/></div>;}
