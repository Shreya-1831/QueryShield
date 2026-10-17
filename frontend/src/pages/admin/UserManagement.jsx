import PageHeader from '../../components/common/PageHeader.jsx';
import UserForm from '../../components/admin/UserForm.jsx';
import { useState } from 'react';
import { useNotifications } from '../../hooks/useNotifications.js';
export default function UserManagement(){const [draft,setDraft]=useState(null);const {notify}=useNotifications();return <><PageHeader eyebrow="ACCESS CONTROL" title="User management" description="User mapping administration requires a secured backend endpoint."/><div className="two-col"><section className="panel"><h3>New mapping draft</h3><UserForm onSubmit={v=>{setDraft(v);notify('Draft prepared only. No server changes were made.','info');}}/></section><section className="panel"><h3>Pending draft</h3>{draft?<pre className="sql-preview">{JSON.stringify(draft,null,2)}</pre>:<p className="muted">No draft prepared.</p>}<p className="muted small">This template intentionally does not persist or submit role changes.</p></section></div></>;}
