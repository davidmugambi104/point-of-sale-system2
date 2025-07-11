import { useState, useEffect } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import api from '../services/api';

const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'timestamp', headerName: 'Timestamp', width: 200 },
  { field: 'user_id', headerName: 'User ID', width: 100 },
  { field: 'action', headerName: 'Action', width: 200 },
  { field: 'details', headerName: 'Details', flex: 1 }
];

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [page, setPage] = useState(1);

  const fetchLogs = async () => {
    try {
      const { data } = await api.get('/audit-logs', {
        params: { page, per_page: 10 }
      });
      setLogs(data.logs);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page]);

  return (
    <div style={{ height: 600, width: '100%' }}>
      <DataGrid
        rows={logs}
        columns={columns}
        pagination
        pageSize={10}
        rowsPerPageOptions={[10]}
        onPageChange={(newPage) => setPage(newPage + 1)}
      />
    </div>
  );
}