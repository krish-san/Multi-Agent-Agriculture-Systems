/**
 * API Service for Multi-Agent Agriculture Systems Demo
 */

const API_BASE_URL = 'http://localhost:8000';

export interface DemoQueryRequest {
  query_text: string;
  language?: string;
  location?: string;
}

export interface DemoQueryResponse {
  status: string;
  query_id: string;
  original_query: string;
  routing_analysis: {
    agent: string;
    confidence: number;
    reasoning: string;
    language_detected: string;
  };
  satellite_data: {
    ndvi: number;
    soil_moisture: number;
    temperature: number;
    humidity: number;
    environmental_score: number;
    risk_level: string;
  };
  response_text: string;
  technical_metrics: {
    processing_time_ms: number;
    confidence_level: number;
    satellite_data_integrated: boolean;
    risk_assessment: string;
    agent: string;
  };
  timestamp: string;
}

export interface DemoCapabilities {
  system_status: string;
  completion_percentage: number;
  operational_agents: string[];
  capabilities: string[];
  satellite_features: string[];
  supported_languages: string[];
}

export interface DemoSession {
  session_id: string;
  start_time: string;
  total_queries: number;
  sample_queries: Array<{
    query: string;
    type: string;
    agent: string;
  }>;
}

class DemoApiService {
  async fetchCapabilities(): Promise<DemoCapabilities> {
    const response = await fetch(`${API_BASE_URL}/demo/capabilities`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  async fetchSession(): Promise<DemoSession> {
    const response = await fetch(`${API_BASE_URL}/demo/session`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  async submitQuery(request: DemoQueryRequest): Promise<DemoQueryResponse> {
    const response = await fetch(`${API_BASE_URL}/demo/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getSampleQueries() {
    const response = await fetch(`${API_BASE_URL}/demo/sample-queries`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  async getAvailableLocations() {
    const response = await fetch(`${API_BASE_URL}/demo/satellite-data`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  async healthCheck() {
    const response = await fetch(`${API_BASE_URL}/demo/health`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
}

export const demoApiService = new DemoApiService();
export default demoApiService;
