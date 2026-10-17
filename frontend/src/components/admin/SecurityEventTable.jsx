
import DataTable from '../app/DataTable.jsx';
import { formatDate } from '../../utils/formatters.js';

export default function SecurityEventTable({ rows = [] }) {
  return (
    <DataTable
      rows={rows}
      columns={[
        {
          key: 'created_at',
          label: 'Time',
          render: (value) => formatDate(value),
        },
        {
          key: 'event_type',
          label: 'Event',
        },
        {
          key: 'severity',
          label: 'Severity',
        },
        {
          key: 'user_id',
          label: 'User',
        },
        {
          key: 'details',
          label: 'Details',
        },
      ]}
    />
  );
}
