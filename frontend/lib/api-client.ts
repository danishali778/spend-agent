import type {
  AnalyzeCaseResponse,
  CreateCaseInput,
  CreateCaseResponse,
  GetActivityResponse,
  GetArtifactsResponse,
  GetCaseResponse,
  GetDecisionResponse,
  ListCasesResponse,
  UploadEmailInput
} from "@spendagent/shared-types";

const API_BASE_URL = process.env.SPENDAGENT_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}

async function requestWithoutJsonHeader<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...init
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}

async function requestOptional<T>(path: string, init?: RequestInit): Promise<T | null> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}

export function listCases() {
  return request<ListCasesResponse>("/cases");
}

export function getCase(caseId: string) {
  return request<GetCaseResponse>(`/cases/${caseId}`);
}

export function getDecision(caseId: string) {
  return requestOptional<GetDecisionResponse>(`/cases/${caseId}/decision`);
}

export function getArtifacts(caseId: string) {
  return requestOptional<GetArtifactsResponse>(`/cases/${caseId}/artifacts`);
}

export function getActivity(caseId: string) {
  return requestOptional<GetActivityResponse>(`/cases/${caseId}/activity`);
}

export function createCase(input: CreateCaseInput) {
  return request<CreateCaseResponse>("/cases", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function analyzeCase(caseId: string) {
  return request<AnalyzeCaseResponse>(`/cases/${caseId}/analyze`, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function uploadEmailDocument(caseId: string, input: UploadEmailInput) {
  return request<{ document: GetCaseResponse["documents"][number] }>(`/cases/${caseId}/documents`, {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function uploadFileDocument(caseId: string, input: {
  type: "contract_pdf" | "invoice_pdf" | "usage_csv";
  sourceName: string;
  file: File;
}) {
  const formData = new FormData();
  formData.append("type", input.type);
  formData.append("sourceName", input.sourceName);
  formData.append("file", input.file);

  return requestWithoutJsonHeader<{ document: GetCaseResponse["documents"][number] }>(`/cases/${caseId}/documents`, {
    method: "POST",
    body: formData
  });
}
