const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "https://3def-2003-df-7f13-1276-b10e-67fb-9555-d049.ngrok-free.app").replace(/\/$/, "");

// ──── Types ────────────────────────────────────────────────────────────────

export interface BearerRefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type UserRole = "reader" | "maintainer" | "admin";

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface IndustryResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface IndustryCreate {
  name: string;
  description?: string | null;
}

export interface IndustryUpdate {
  name?: string | null;
  description?: string | null;
}

export interface CompanyResponse {
  id: string;
  name: string;
  industry_id: string;
  description: string | null;
  website: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompanyCreate {
  name: string;
  industry_id: string;
  description?: string | null;
  website?: string | null;
}

export interface CompanyUpdate {
  name?: string | null;
  industry_id?: string | null;
  description?: string | null;
  website?: string | null;
}

export type TranscriptStatus = "uploaded" | "processing" | "completed" | "failed";

export interface TranscriptResponse {
  id: string;
  filename: string;
  company_id: string;
  uploaded_by_id: string;
  status: TranscriptStatus;
  task_id: string | null;
  chunk_count: number | null;
  chunks_processed: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export type UseCaseStatus = "new" | "under_review" | "approved" | "in_progress" | "completed" | "archived";

export interface UseCaseResponse {
  id: string;
  title: string;
  description: string;
  expected_benefit: string | null;
  tags: string[] | null;
  company_id: string;
  transcript_id: string | null;
  assignee_id: string | null;
  created_by_id: string;
  status: UseCaseStatus;
  confidence_score: number;
  effort_score: number | null;
  impact_score: number | null;
  complexity_score: number | null;
  strategic_score: number | null;
  priority_score: number | null;
  qdrant_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface UseCaseCreate {
  title: string;
  description: string;
  expected_benefit?: string | null;
  tags?: string[] | null;
  company_id: string;
  transcript_id?: string | null;
}

export interface UseCaseUpdate {
  title?: string | null;
  description?: string | null;
  expected_benefit?: string | null;
  tags?: string[] | null;
}

export interface UseCaseScoresUpdate {
  effort_score?: number | null;
  impact_score?: number | null;
  complexity_score?: number | null;
  strategic_score?: number | null;
}

export interface UseCaseStatusUpdate {
  status: UseCaseStatus;
}

export interface UseCaseAssigneeUpdate {
  assignee_id: string | null;
}

export type RelationType = "depends_on" | "complements" | "conflicts_with" | "duplicates";

export interface UseCaseRelationCreate {
  target_id: string;
  relation_type: RelationType;
  note?: string | null;
}

export interface CommentResponse {
  id: string;
  body: string;
  use_case_id: string;
  author_id: string;
  created_at: string;
  updated_at: string;
}

export interface CommentCreate {
  body: string;
}

export interface SearchQuery {
  query: string;
  filters?: Record<string, unknown> | null;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ErrorModel {
  detail: string | Record<string, string>;
}

// ──── Token helpers ────────────────────────────────────────────────────────

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// ──── Generic fetcher ──────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
    "ngrok-skip-browser-warning": "true",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        const refreshRes = await fetch(`${API_BASE}/auth/jwt/refresh`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true",
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (refreshRes.ok) {
          const data: BearerRefreshResponse = await refreshRes.json();
          setTokens(data.access_token, data.refresh_token);
          headers["Authorization"] = `Bearer ${data.access_token}`;
          const retryRes = await fetch(`${API_BASE}${path}`, { ...options, headers });
          if (!retryRes.ok) {
            const err = await retryRes.json().catch(() => ({ detail: "Request failed" }));
            throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
          }
          if (retryRes.status === 204) return undefined as T;
          return retryRes.json();
        }
      } catch {
        clearTokens();
        if (typeof window !== "undefined") window.location.href = "/login";
        throw new Error("Session expired");
      }
    }
    clearTokens();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ──── Auth ─────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<BearerRefreshResponse> {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_BASE}/auth/jwt/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "ngrok-skip-browser-warning": "true",
    },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Login failed");
  }
  return res.json();
}

export async function register(
  email: string,
  password: string,
  fullName?: string
): Promise<UserResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
    },
    body: JSON.stringify({ email, password, full_name: fullName || undefined }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Registration failed");
  }
  return res.json();
}

export async function logout(): Promise<void> {
  await apiFetch("/auth/jwt/logout", { method: "POST" });
  clearTokens();
}

export async function getMe(): Promise<UserResponse> {
  return apiFetch<UserResponse>("/auth/me");
}

export async function listUsers(page = 1, pageSize = 20) {
  return apiFetch<PaginatedResponse<UserResponse>>(`/auth/users?page=${page}&page_size=${pageSize}`);
}

export async function getUser(userId: string): Promise<UserResponse> {
  return apiFetch<UserResponse>(`/auth/users/${userId}`);
}

export async function deleteUser(userId: string): Promise<void> {
  return apiFetch<void>(`/auth/users/${userId}`, { method: "DELETE" });
}

export async function updateUserRole(userId: string, role: UserRole): Promise<UserResponse> {
  return apiFetch<UserResponse>(`/auth/users/${userId}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

// ──── Industries ───────────────────────────────────────────────────────────

export async function listIndustries(page = 1, pageSize = 100) {
  return apiFetch<PaginatedResponse<IndustryResponse>>(`/industries?page=${page}&page_size=${pageSize}`);
}

export async function getIndustry(id: string): Promise<IndustryResponse> {
  return apiFetch<IndustryResponse>(`/industries/${id}`);
}

export async function createIndustry(data: IndustryCreate): Promise<IndustryResponse> {
  return apiFetch<IndustryResponse>("/industries", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateIndustry(id: string, data: IndustryUpdate): Promise<IndustryResponse> {
  return apiFetch<IndustryResponse>(`/industries/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteIndustry(id: string): Promise<void> {
  return apiFetch<void>(`/industries/${id}`, { method: "DELETE" });
}

// ──── Companies ────────────────────────────────────────────────────────────

export async function listCompanies(page = 1, pageSize = 100, industryId?: string, q?: string) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (industryId) params.set("industry_id", industryId);
  if (q) params.set("q", q);
  return apiFetch<PaginatedResponse<CompanyResponse>>(`/companies?${params}`);
}

export async function getCompany(id: string): Promise<CompanyResponse> {
  return apiFetch<CompanyResponse>(`/companies/${id}`);
}

export async function createCompany(data: CompanyCreate): Promise<CompanyResponse> {
  return apiFetch<CompanyResponse>("/companies", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateCompany(id: string, data: CompanyUpdate): Promise<CompanyResponse> {
  return apiFetch<CompanyResponse>(`/companies/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteCompany(id: string): Promise<void> {
  return apiFetch<void>(`/companies/${id}`, { method: "DELETE" });
}

// ──── Transcripts ──────────────────────────────────────────────────────────

export async function listTranscripts(
  page = 1,
  pageSize = 100,
  companyId?: string,
  status?: TranscriptStatus
) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (companyId) params.set("company_id", companyId);
  if (status) params.set("status", status);
  return apiFetch<PaginatedResponse<TranscriptResponse>>(`/transcripts?${params}`);
}

export async function getTranscript(id: string): Promise<TranscriptResponse> {
  return apiFetch<TranscriptResponse>(`/transcripts/${id}`);
}

export async function uploadTranscript(file: File, companyId: string): Promise<TranscriptResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("company_id", companyId);
  return apiFetch<TranscriptResponse>("/transcripts", {
    method: "POST",
    body: formData,
  });
}

export async function deleteTranscript(id: string): Promise<void> {
  return apiFetch<void>(`/transcripts/${id}`, { method: "DELETE" });
}

export async function reprocessTranscript(id: string): Promise<void> {
  return apiFetch<void>(`/transcripts/${id}/reprocess`, { method: "POST" });
}

// SSE stream for transcript progress
export function subscribeTranscriptProgress(
  transcriptId: string,
  onMessage: (data: unknown) => void,
  onError?: (err: Event) => void
): EventSource {
  const url = `${API_BASE}/transcripts/${transcriptId}/events`;
  const es = new EventSource(url);
  es.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data));
    } catch {
      onMessage(e.data);
    }
  };
  if (onError) es.onerror = onError;
  return es;
}

// ──── Use Cases ────────────────────────────────────────────────────────────

export async function listUseCases(params?: {
  page?: number;
  page_size?: number;
  company_id?: string;
  industry_id?: string;
  status?: UseCaseStatus;
  assignee_id?: string;
  min_confidence?: number;
  tags?: string;
  q?: string;
  sort_by?: string;
  order?: string;
}) {
  const sp = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
    });
  }
  if (!sp.has("page")) sp.set("page", "1");
  if (!sp.has("page_size")) sp.set("page_size", "100");
  return apiFetch<PaginatedResponse<UseCaseResponse>>(`/use-cases?${sp}`);
}

export async function getUseCase(id: string): Promise<UseCaseResponse> {
  return apiFetch<UseCaseResponse>(`/use-cases/${id}`);
}

export async function createUseCase(data: UseCaseCreate): Promise<UseCaseResponse> {
  return apiFetch<UseCaseResponse>("/use-cases", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateUseCase(id: string, data: UseCaseUpdate): Promise<UseCaseResponse> {
  return apiFetch<UseCaseResponse>(`/use-cases/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteUseCase(id: string): Promise<void> {
  return apiFetch<void>(`/use-cases/${id}`, { method: "DELETE" });
}

export async function updateUseCaseStatus(id: string, status: UseCaseStatus): Promise<UseCaseResponse> {
  return apiFetch<UseCaseResponse>(`/use-cases/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function updateUseCaseScores(id: string, data: UseCaseScoresUpdate): Promise<UseCaseResponse> {
  return apiFetch<UseCaseResponse>(`/use-cases/${id}/scores`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function updateUseCaseAssignee(id: string, assigneeId: string | null): Promise<UseCaseResponse> {
  return apiFetch<UseCaseResponse>(`/use-cases/${id}/assignee`, {
    method: "PATCH",
    body: JSON.stringify({ assignee_id: assigneeId }),
  });
}

export async function createUseCaseRelation(useCaseId: string, data: UseCaseRelationCreate) {
  return apiFetch(`/use-cases/${useCaseId}/relations`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteUseCaseRelation(useCaseId: string, relationId: string): Promise<void> {
  return apiFetch<void>(`/use-cases/${useCaseId}/relations/${relationId}`, { method: "DELETE" });
}

// ──── Comments ─────────────────────────────────────────────────────────────

export async function listComments(useCaseId: string, page = 1, pageSize = 100) {
  return apiFetch<PaginatedResponse<CommentResponse>>(
    `/use-cases/${useCaseId}/comments?page=${page}&page_size=${pageSize}`
  );
}

export async function createComment(useCaseId: string, body: string): Promise<CommentResponse> {
  return apiFetch<CommentResponse>(`/use-cases/${useCaseId}/comments`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export async function updateComment(useCaseId: string, commentId: string, body: string): Promise<CommentResponse> {
  return apiFetch<CommentResponse>(`/use-cases/${useCaseId}/comments/${commentId}`, {
    method: "PATCH",
    body: JSON.stringify({ body }),
  });
}

export async function deleteComment(useCaseId: string, commentId: string): Promise<void> {
  return apiFetch<void>(`/use-cases/${useCaseId}/comments/${commentId}`, { method: "DELETE" });
}

// ──── Search ───────────────────────────────────────────────────────────────

export async function searchUseCases(data: SearchQuery) {
  return apiFetch<Record<string, unknown>>("/search/use-cases", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function findSimilar(useCaseId: string, limit = 10) {
  return apiFetch<Record<string, unknown>>(`/search/similar/${useCaseId}?limit=${limit}`);
}

export async function crossIndustryTheme(theme: string) {
  return apiFetch<Record<string, unknown>>(`/search/cross-industry?theme=${encodeURIComponent(theme)}`, {
    method: "POST",
  });
}
