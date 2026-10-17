
import api from './apiClient.js';

// Users
export async function getUsers(employeeId) {
  if (employeeId) {
    const { data } = await api.get(
      `/api/users/${encodeURIComponent(employeeId)}`
    );
    return data;
  }

  // The backend exposes /api/admin/users for listing users.
  const { data } = await api.get('/api/admin/users');
  return data;
}

// Audit logs
export async function getAuditLogs() {
  const { data } = await api.get('/api/admin/audit');
  return data;
}


/* Security events */
export async function getSecurityEvents() {
  const { data } = await api.get('/api/admin/security-events', {
    params: { limit: 50 },
  });

  return data.events ?? [];
}


// Alerts
export async function getAlerts() {
  const { data } = await api.get('/alerts');
  return data;
}

// AI models
export async function getModels() {
  const { data } = await api.get('/api/admin/models');
  return data;
}

// Permissions
export async function getPermissions(employeeId) {
  if (!employeeId) {
    throw new Error('An employee ID is required to retrieve permissions.');
  }

  const { data } = await api.get(
    `/api/permissions/${encodeURIComponent(employeeId)}`
  );
  return data;
}
