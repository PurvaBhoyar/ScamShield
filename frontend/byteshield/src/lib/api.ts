interface Finding {
  type: string;
  severity: string;
  message: string;
}

interface DomainInfo {
  domain?: string;
  registered?: boolean;
  registrar?: string;
  creation_date?: string;
  expiration_date?: string;
  age_days?: number;
  registrar_country?: string;
}

interface DomainReason {
  type: string;
  severity: string;
  message: string;
}

export interface ScanResponse {
  id: string;
  company_name: string;
  job_title: string;
  location: string;
  score: number;
  label: string;
  findings: Finding[];
  evidence: string[];
  actions: string[];
  createdAt: string;
  domain?: string;
  domain_info?: DomainInfo;
  domain_reasons?: DomainReason[];
}

export type ScanType = 'url' | 'text' | 'file';

interface ScanParams {
  type: ScanType;
  url?: string;
  text?: string;
  file?: File;
}

export async function scanContent(params: ScanParams): Promise<ScanResponse> {
  const formData = new FormData();
  formData.append('type', params.type);

  if (params.type === 'url' && params.url) {
    formData.append('url', params.url);
  } else if (params.type === 'text' && params.text) {
    formData.append('text', params.text);
  } else if (params.type === 'file' && params.file) {
    formData.append('file', params.file);
  }

  const response = await fetch('/api/scan', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Scan failed with status ${response.status}`);
  }

  return response.json();
}