export function getErrorMessage(error, fallback='Something went wrong.') {
  return error?.userMessage || error?.response?.data?.detail || error?.message || fallback;
}
