import createClient from "openapi-fetch";
import type { paths } from "./schema";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient = createClient<paths>({ baseUrl });
