import PageHeader from '../../components/common/PageHeader.jsx';
import PermissionEditor from '../../components/admin/PermissionEditor.jsx';
import { useNotifications } from '../../hooks/useNotifications.js';
export default function Permissions(){const {notify}=useNotifications();return <><PageHeader eyebrow="POLICY" title="Permissions & policies" description="Review a policy draft. Connect this interface only to a validated, authorized backend policy-management endpoint."/><PermissionEditor onSave={()=>notify('Policy draft only. No backend policy was changed.','info')}/></>;}
