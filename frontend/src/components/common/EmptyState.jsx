import { Inbox } from 'lucide-react';
export default function EmptyState({title='Nothing here yet',description='Data will appear here when available.'}){return <div className="state-card"><Inbox size={28}/><h3>{title}</h3><p>{description}</p></div>;}
