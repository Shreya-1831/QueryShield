import DataTable from '../app/DataTable.jsx';
import { formatDate } from '../../utils/formatters.js';
export default function AuditTable({rows=[]}){const columns=[{key:'timestamp',label:'Time',render:v=>formatDate(v)},{key:'username',label:'User'},{key:'action',label:'Action'},{key:'decision',label:'Decision'},{key:'risk',label:'Risk'}];return <DataTable columns={columns} rows={rows}/>;}
