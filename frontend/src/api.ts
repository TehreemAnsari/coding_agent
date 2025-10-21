const API_BASE = '/api';

export interface TestCase {
  input: string;
  expected_output: string;
  output: string | null;
  passed: boolean;
  error: string | null;
  runtime_ms: number | null;
}

export interface GenerateResponse {
  id: string;
  solution_code: string;
  results: TestCase[];
  score: number;
  error: string | null;
}

export interface RunSummary {
  run_id: string;
  timestamp: string;
  score: number;
  problem_preview: string;
}

export async function generateSolution(problem: string, testCases: any[][]): Promise<GenerateResponse> {
  const response = await fetch(`${API_BASE}/generate_solution`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      problem,
      test_cases: testCases,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate solution');
  }

  return response.json();
}

export async function getRuns(limit: number = 20): Promise<RunSummary[]> {
  const response = await fetch(`${API_BASE}/runs?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch runs');
  }
  return response.json();
}

export async function getResult(runId: string): Promise<any> {
  const response = await fetch(`${API_BASE}/results/${runId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch result');
  }
  return response.json();
}
