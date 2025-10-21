import { useState } from 'react'
import { generateSolution, getRuns, type GenerateResponse, type RunSummary } from './api'
import './App.css'

function App() {
  const [problem, setProblem] = useState('')
  const [testCases, setTestCases] = useState('[\n  [[1, 2], 3],\n  [[10, 20], 30]\n]')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [showHistory, setShowHistory] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const parsedTestCases = JSON.parse(testCases)
      const response = await generateSolution(problem, parsedTestCases)
      setResult(response)
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const loadHistory = async () => {
    try {
      const history = await getRuns()
      setRuns(history)
      setShowHistory(true)
    } catch (err: any) {
      setError(err.message || 'Failed to load history')
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Code-Solver Agent</h1>
        <p>AI-powered coding problem solver</p>
      </header>

      <div className="container">
        <div className="main-content">
          <form onSubmit={handleSubmit} className="input-form">
            <div className="form-group">
              <label htmlFor="problem">Coding Problem:</label>
              <textarea
                id="problem"
                value={problem}
                onChange={(e) => setProblem(e.target.value)}
                placeholder="e.g., Write a function that returns the sum of two numbers"
                rows={4}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="testCases">Test Cases (JSON):</label>
              <textarea
                id="testCases"
                value={testCases}
                onChange={(e) => setTestCases(e.target.value)}
                placeholder='[[[arg1, arg2, ...], expected_output], ...]'
                rows={6}
                required
              />
              <small>Format: [[[inputs...], expected], ...]</small>
            </div>

            <div className="button-group">
              <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? 'Generating...' : 'Generate Solution'}
              </button>
              <button type="button" onClick={loadHistory} className="btn btn-secondary">
                View History
              </button>
            </div>
          </form>

          {error && (
            <div className="error-box">
              <strong>Error:</strong> {error}
            </div>
          )}

          {result && (
            <div className="result-section">
              <div className="result-header">
                <h2>Solution Generated</h2>
                <div className="score">
                  Score: {(result.score * 100).toFixed(0)}%
                </div>
              </div>

              {result.error && (
                <div className="error-box">
                  <strong>Generation Error:</strong> {result.error}
                </div>
              )}

              <div className="code-section">
                <h3>Generated Code:</h3>
                <pre className="code-block">
                  <code>{result.solution_code}</code>
                </pre>
              </div>

              <div className="results-table-container">
                <h3>Test Results:</h3>
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Input</th>
                      <th>Expected</th>
                      <th>Output</th>
                      <th>Status</th>
                      <th>Time (ms)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.results.map((tc, idx) => (
                      <tr key={idx} className={tc.passed ? 'passed' : 'failed'}>
                        <td>{idx + 1}</td>
                        <td>{tc.input}</td>
                        <td>{tc.expected_output}</td>
                        <td>{tc.error ? <span className="error-text">{tc.error}</span> : tc.output}</td>
                        <td>
                          <span className={`status ${tc.passed ? 'status-pass' : 'status-fail'}`}>
                            {tc.passed ? '✓ Pass' : '✗ Fail'}
                          </span>
                        </td>
                        <td>{tc.runtime_ms}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {showHistory && (
          <div className="history-panel">
            <div className="history-header">
              <h2>Run History</h2>
              <button onClick={() => setShowHistory(false)} className="btn-close">×</button>
            </div>
            <div className="history-list">
              {runs.length === 0 ? (
                <p className="empty-message">No runs yet</p>
              ) : (
                runs.map((run) => (
                  <div key={run.run_id} className="history-item">
                    <div className="history-item-header">
                      <span className="run-score">{(run.score * 100).toFixed(0)}%</span>
                      <span className="run-time">{new Date(run.timestamp).toLocaleString()}</span>
                    </div>
                    <p className="run-problem">{run.problem_preview}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
