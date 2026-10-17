import { BellRing } from 'lucide-react';
import StatusBadge from '../app/StatusBadge.jsx';
export default function AlertList({items=[]}){if(!items.length)return <p className="muted">No alerts returned by the API.</p>;return <div className="alert-list">{items.map((a,i)=><article className="alert-row" key={a.id||i}><BellRing size={18}/><div><strong>{a.title||a.message||a.type||'System alert'}</strong><p>{a.description||a.detail||''}</p></div><StatusBadge status={a.severity||a.status||'info'}/></article>)}</div>;}
