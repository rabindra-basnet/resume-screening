import axios from "axios";

// The API lives on the same origin as the FastAPI app.
export const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err?.response?.data?.detail;
    const status = err?.response?.status;
    const message =
      typeof detail === "string" ? detail : detail?.message || err?.message || "Request failed";
    if (status === 401 && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    return Promise.reject(new Error(message));
  },
);

export async function apiGet<T>(path: string): Promise<T> {
  const res = await api.get<T>(path);
  return res.data;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await api.post<T>(path, body);
  return res.data;
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const res = await api.post<T>(path, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export function errMsg(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}
