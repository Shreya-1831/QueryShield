import * as Icons from 'lucide-react';
export default function StatCard({label,value,detail,icon='Activity'}){const Icon=Icons[icon]||Icons.Activity;return <article className="stat-card"><div className="stat-card-top"><span>{label}</span><span className="stat-icon"><Icon size={19}/></span></div><strong>{value??'—'}</strong>{detail&&<p>{detail}</p>}</article>;}
