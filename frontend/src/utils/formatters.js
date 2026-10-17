export function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(date);
}
export function formatNumber(value) { return new Intl.NumberFormat().format(Number(value || 0)); }
export function humanize(value='') { return String(value).replace(/[_-]+/g,' ').replace(/\b\w/g, c => c.toUpperCase()); }
