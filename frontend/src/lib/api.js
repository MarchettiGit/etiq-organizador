import axios from "axios";

export const api = axios.create({ baseURL: `${process.env.REACT_APP_BACKEND_URL}/api` });

export const errorMessage = async (err, fallback = "Ocorreu um erro") => {
  const data = err?.response?.data;
  if (data instanceof Blob) {
    try {
      return JSON.parse(await data.text()).detail || fallback;
    } catch {
      return fallback;
    }
  }
  return data?.detail || fallback;
};

export const downloadJob = async (job) => {
  const res = await api.get(`/jobs/${job.id}/download`, { responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = job.filename.replace(/\.pdf$/i, "") + "_organizado.pdf";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

export const formatDate = (iso) =>
  new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

export const USER_KEY = "oe_user_name";
