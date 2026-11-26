// One function for all calls to the backend. It adds the login token for us.

export const getToken = () => localStorage.getItem("token");

export async function api(path, { method = "GET", body, raw = false } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`;

  const response = await fetch("/api" + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Token expired or account disabled: go back to the login page
  if (response.status === 401 && !path.startsWith("/auth/login")) {
    localStorage.removeItem("token");
    window.location.href = "/login";
  }
  if (raw) return response;

  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(errorText(data));
  return data;
}

// The server sends errors as text, or as a list when a form field is wrong.
function errorText(data) {
  const detail = data && data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) return "Please check the form: " + detail[0].msg;
  return "Something went wrong";
}
