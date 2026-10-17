export function normalizeRole(user) {
  return String(user?.role || user?.user_type || user?.type || '').toLowerCase();
}
export function isAdmin(user) { return normalizeRole(user) === 'admin'; }
export function canAccessApp(status) { return status === 'authenticated'; }
