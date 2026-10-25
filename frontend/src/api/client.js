let accessToken = "";

export function setAccessToken(token) {
  accessToken = token;
}

export async function apiRequest(
  path,
  { method = "GET", body, signal } = {},
) {
  const headers = {};

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(`/api${path}`, {
    method,
    headers,
    signal,
    ...(body !== undefined
      ? { body: JSON.stringify(body) }
      : {}),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));

    const message = Array.isArray(data.detail)
      ? data.detail.map((error) => error.msg).join("; ")
      : data.detail || `Request failed (${response.status})`;

    const error = new Error(message);
    error.status = response.status;

    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}