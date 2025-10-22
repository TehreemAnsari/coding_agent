# Code-Solver Agent

This is a solution to the problem statement [given here](https://hexoai.notion.site/SWE-interview-task-28989b90df088061990ecd83214c71e9).
This solution is a full-stack AI-powered coding problem solver that uses LLMs to generate Python solutions, executes them against test cases, and provides detailed scoring and results.

## Features
As per the problem, I was required to have these **Deliverables (functional requirements) + evaluation criteria**
| # | Component | Status |
|---|------------|--------|
| 1 | Autonomous agent (problem solver + test runner + scorer) | Done see 1 & 2 points below |
| 2 | Eval metric calculated on the evaluation set | Done see eval_set.json and evaluate.py |
| 3 | API endpoints and data persistence | Done see point 7. API endpoints and 8. Run history |
| 4 | Frontend chat UI integration | Done see point 5. Web UI (Frontend) |
| 5 | A [README.md](README.md) with instruction to use and proper code documentation | Done (this file is the readme) |
| 6 | Code Quality | Done (generic SDE principles like safety, modularity, class based for extension to other LLMs) see Project structure section onwards |
| 7 | Architecture | Done see Architecture section below |

These are covered in the below points 1-8. The readme is this file you are reading.
## **1. AI Code Generation** 
Part of Autonomous agent > problem solver

**File:** `backend/app/llm.py`
**Functions:**

* `call_llm()` → Calls OpenAI’s API
* `build_messages()` → Prepares structured prompt

**Key logic:**

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    temperature=0.0,
    max_tokens=1200,
)
content = response.choices[0].message.content
```
**Explaination**
1. `client`: an instance of `OpenAI(api_key=...)`.

2. `.chat.completions.create()`: calls the Chat Completions API endpoint, which powers models like `gpt-4o`, `gpt-4o-mini`, etc. This generates a `response` based on the chat history (messages).

3. Arguments
- model=	Which model to use (`gpt-4o-mini` here as mentioned in local setup).
- messages=messages	A list of message dictionaries like:
[{"role": "system", "content": "...instructions..."}, {"role": "user", "content": "...problem text..."}]
- temperature=0.0	Controls randomness. 0 → fully deterministic (ideal for code).
- max_tokens=1200	Caps the length of generated output (here, up to 1200 tokens).
3. Response Object Structure

OpenAI API returns a structured object like:

    {
       "id": "chatcmpl-xyz",
      "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "def solve(...): ..."
      },
      "finish_reason": "stop"
    }
  ],
      "usage": {...}
    }


So:

`response.choices[0].message.content` extracts the actual generated text (the "def solve(...): ..." which is the code, it's similar to asking chatgpt chat interface, give me python code to add 2 numbers, but here we are doing via code).


---

## **2. Automated Testing**
Part of test runner + scorer

**File:** `backend/app/runner.py`
**Method:** `run_tests()`

**Key logic & explaination:**

```python
def run_tests(self, problem_text: str, generated_code: str,
              test_cases: List[Tuple[List[Any], Any]],
              llm_trajectory=None, timeout: Optional[int] = None) -> Dict[str, Any]:
... (full code in github runner.py, plz refer that)

ok, stdout, stderr, runtime_ms = self._exec_solution(solution_path, payload, exec_timeout)
```
This function does the below important tasks:
- It takes a problem, a generated Python solution (from 1), and a list of test cases, and returns a structured report showing which tests passed, failed, or crashed. 
- `_make_solution_file()` writes the generated Python code (a string) to a temporary file on disk (here `os.path.join(tmpdir, "solution.py")`).
- Iterate through each test case here `for inp, expected in test_cases:...`
- _exec_solution() runs the generated Python file in a separate subprocess for safety (also see 3 for more details).
- Compare with expected result
- Record each test case result
---

## **3. Safety**

**File:** `backend/app/runner.py`
**Methods:**

* `_validate_code_safety()`
* `_make_solution_file()`
* `_exec_solution()`

**Key logic:**

**Sandboxing/isolation:**
CodeRunner has three main layers working together:
1. Safety Layer: `_validate_code_safety()`: Blocks unsafe imports and keywords before running anything.
2. Sandbox Layer : `_make_solution_file()`: Wraps the LLM-generated code in a controlled execution environment (a wrapper script).
3. Subprocess Layer : `_exec_solution()` Executes that wrapper script in a separate process using subprocess.run.

```python
[ FastAPI Server / Main Process ]
          │
          ▼
    run_tests()  ─────────────────────────────────────┐
          │                                           │
          ▼                                           │
   _make_solution_file() writes wrapper to /tmp       │
          │                                           │
          ▼                                           │
  _exec_solution()  →  subprocess.run("python /tmp/solution.py …")
          │
          ▼
  [ Subprocess / Sandbox Environment ]
       - Only stdlib imports allowed
       - Only JSON I/O
       - No access to filesystem / network / OS
       - Timeout-enforced kill
```
These create a sandbox for automated testing and isolation.

**Other security:**
```python
if pattern.lower() in code_lower:
    raise RuntimeError(f"Blocked potentially unsafe code pattern: {pattern}")
```
- Blocks imports like `os`, `subprocess`, `socket`, etc.
- Enforces timeout, catches exceptions safely.

---

## **4. JSON Logging**

**File:** `backend/app/runner.py`
**Method:** `run_tests()`
**Output Path:** `/backend/runs/run_<timestamp>.json`

 **Key logic:**

```python
return {
  "run_id": str(int(time.time() * 1000)),
  "timestamp": datetime.utcnow().isoformat() + "Z",
  "problem_text": problem_text,
  "solution_code": generated_code,
  "test_cases": results,
  "score": score,
}
```

- Each run is serialized to JSON and saved under `/runs`.

---

## **5. Web UI (Frontend)**

**Folder:** `frontend/`
**Files:**

* `App.tsx` — Chat-like interface (problem + test cases input)
* `api.ts` — Calls backend endpoints
* `main.tsx` — Renders root React app
* `index.html` — Static entry

 **Key logic:**

```typescript
const res = await generateSolution(problem, testCases);
setResults(res);
```

- Sends POST to `/generate_solution`
- Displays generated code, test results, and score in a neat chat interface.

---

##  **6. CLI Interface**

**File:** `backend/app/cli.py`
**Lines:** ~10–50 (may change later, these were lines when I updated on 22nd Oct)

 **Key logic:**

```python
python -m app.cli --problem "Reverse a string" --test-cases '[[["abc"], "cba"]]'
```

- Uses `argparse` to take problem + test cases
- Calls `solve_problem()` and prints formatted output with score + run_id.

---

##  **7. API Endpoints**

**File:** `backend/app/main.py`
**Lines:** ~5–30  (may change later, these were lines when I updated on 22nd Oct)
**Routers:**

* `/generate_solution` → `routes_generate.py`
* `/results/{id}` → `routes_results.py`

 **Key logic:**

```python
app.include_router(generate_router)
app.include_router(results_router)
```

- FastAPI automatically builds `/openapi.json` and Swagger docs
- Responses follow schema defined in route handlers.

---

## **8. Run History**

**Folder:** `/backend/runs`
**File:** `app/utils/file_ops.py` (if implemented) or inline in `runner.py`

 **Key logic:**

```python
list_runs()  # returns JSON metadata of past runs
load_run(run_id)  # retrieves full log details
```

- All runs are timestamped, retrievable through `/results/{id}`
- Frontend fetches and lists history (like "Previous Runs" section).

---

## ** Architecture **

It's roughly a **3.5-tier system**:

1. **Frontend (React + Tailwind (css))** — user-facing chat
2. **Backend (FastAPI)** — API + code orchestration
3. **Executor Layer (Runner + LLM)** — actual agent engine
3.5. **Storage** - Rightnow it's on local storage via /runs, can be stored to cloud too in future.

```python
                        System Architecture
───────────────────────────────────────────────────────────────────────────────
                                  [ User Interface Layer ]
───────────────────────────────────────────────────────────────────────────────
                                 Frontend
                             --------------------------------
                             |  - Problem + Test case input  |
                             |  - Displays generated code    |
                             |  - Shows pass/fail results    |
                             |  - Lists past runs (history)  |
                             --------------------------------
                                          │
                                          ▼
                          (HTTP requests in api.ts) (CLI/Direct API via browser)
                                          │
                                          ▼
───────────────────────────────────────────────────────────────────────────────
                                   [ API Gateway Layer ]
───────────────────────────────────────────────────────────────────────────────
                              FastAPI Backend (app/main.py)
                           -------------------------------------
                           |  /generate_solution   (POST)      |
                           |     → calls Agent + Runner        |
                           |  /results/{id}       (GET)        |
                           |     → loads saved run JSON        |
                           -------------------------------------
                                          │
                                          ▼
───────────────────────────────────────────────────────────────────────────────
                                [ Core Agent Logic Layer ]
───────────────────────────────────────────────────────────────────────────────
                     agent.py — Orchestrator
                   --------------------------
                   | - Accepts problem text  |
                   | - Parses test cases     |
                   | - Calls LLM + Runner    |
                   --------------------------
                              │             │
                              ▼             ▼
       llm.py (AI Code Generation)       runner.py (Testing Engine)
      ------------------------------     ------------------------------
      | - Uses OpenAI API               | - Creates safe temp file     |
      | - Reads prompt_template.txt     | - Runs subprocess            |
      | - Builds solve() function       | - Applies timeouts & safety  |
      | - Returns generated code        | - Captures stdout/stderr     |
      ------------------------------     | - Calculates score/pass rate|
                                          ------------------------------
                              │
                              ▼
───────────────────────────────────────────────────────────────────────────────
                                   [ Data Persistence Layer ]
───────────────────────────────────────────────────────────────────────────────
                          /runs/  (Local JSON-based Run History)
                         -----------------------------------------
                         |  run_<timestamp>.json                 |
                         |   {                                   |
                         |     "problem_text": "...",            |
                         |     "solution_code": "...",           |
                         |     "results": [...],                 |
                         |     "score": 0.85,                    |
                         |     "error": null                     |
                         |   }                                   |
                         -----------------------------------------
                                          │
                                          ▼
───────────────────────────────────────────────────────────────────────────────
                              [ Evaluation Workflow ]
───────────────────────────────────────────────────────────────────────────────
 📊 evaluate.py
 -----------------------------
 | - Loads eval_set.json      |
 | - Calls agent for each     |
 | - Aggregates total score   |
 | - Prints "Final Eval Score"|
 -----------------------------
───────────────────────────────────────────────────────────────────────────────
```

## Project Structure

```
code-solver-agent/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   │   ├── __init__.py
│   │   │   ├── routes_generate.py  # Solution generation endpoints
│   │   │   └── routes_results.py  # Results and history endpoints
│   │   ├── core/             # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── agent.py      # Main agent orchestration logic
│   │   │   ├── llm.py        # OpenAI client wrapper
│   │   │   └── runner.py     # Code execution engine
│   │   ├── models/           # Pydantic data models
│   │   │   ├── __init__.py
│   │   │   └── problem.py    # Request/response schemas
│   │   ├── utils/            # Utility functions
│   │   │   ├── __init__.py
│   │   │   └── file_ops.py   # File operations and persistence
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application
│   │   └── cli.py            # CLI interface
│   ├── runs/                 # Stored run results (JSON)
│   ├── eval_set.json         # Benchmark evaluation set
│   ├── evaluate.py           # Evaluation script
│   ├── cli.py                # Standalone CLI entry point
│   └── requirements.txt      # Python dependencies
└── frontend/
    ├── src/
    │   ├── App.tsx           # Main React component
    │   ├── App.css           # Component styles
    │   ├── api.ts            # API client
    │   ├── index.css         # Global styles
    │   └── main.tsx          # Entry point
    ├── index.html            # HTML template
    ├── package.json          # Node.js dependencies
    ├── tsconfig.json         # TypeScript configuration
    ├── tsconfig.node.json    # Node TypeScript configuration
    └── vite.config.ts        # Vite build configuration
```

## Code Organization

### **Modular Architecture**
- **`api/`** - FastAPI route handlers organized by functionality
- **`core/`** - Core business logic (agent, LLM, code execution)
- **`models/`** - Pydantic data models and schemas
- **`utils/`** - Utility functions for file operations and persistence

### **Enhanced Imports**
The `__init__.py` files have been enhanced to provide convenient imports

## Setup

1. **Environment Variables**: Open AI secret

2. **Install Dependencies**: requirement.txt

3. **Run the Application**: (See below for how to run on local)

---------------
# Explaination of all the files (at a file level) 
(this is what I updated on 22nd Oct, new files may be added in future)

## Backend Files (`/backend/`)

### Core Application Files (`/backend/app/`)

### `main.py` - FastAPI Application

- **Purpose**: Main FastAPI server with REST API endpoints
- **Key Features**:
    - CORS middleware for frontend communication
    - `POST /generate_solution` - Generates and tests AI solutions
    - `GET /results/{run_id}` - Retrieves specific run results
    - `GET /runs` - Lists recent runs with summaries
- **Dependencies**: Uses models, agent, and storage modules

### `agent.py` - Core Orchestration Logic

- **Purpose**: Main business logic for problem solving workflow
- **Key Functions**:
    - `parse_test_cases()` - Validates and parses test case format
    - `solve_problem()` - Orchestrates the entire solve process:
        1. Calls LLM to generate code
        2. Executes code against test cases
        3. Optionally performs self-reflection loops for failed cases
        4. Saves results to storage
- **Features**: Supports self-reflection with retry logic

### `llm.py` - OpenAI Integration

- **Purpose**: Handles all LLM interactions with OpenAI
- **Key Features**:
    - Loads system prompt from `prompt_template.txt` or uses default
    - Builds structured messages for OpenAI API
    - Extracts Python code from LLM responses (handles markdown code blocks)
    - Configurable model (defaults to `gpt-4o-mini`)
- **Security**: Uses environment variables for API key

### `runner.py` - Code Execution Engine

- **Purpose**: Safely executes generated Python code
- **Key Features**:
    - **Security**: Comprehensive safety checks:
        - Import allowlist (only safe standard library modules)
        - Pattern-based blocking of dangerous operations
        - Timeout controls (6 seconds per test)
    - **Execution Strategy**: Multiple fallback approaches for function calling
    - **Wrapper Generation**: Creates CLI-friendly scripts for subprocess execution
    - **Result Processing**: JSON-based input/output handling
- **Safety**: Blocks file I/O, subprocess, eval, exec, and other dangerous operations

### `models.py` - Pydantic Data Models

- **Purpose**: Defines API request/response schemas
- **Key Models**:
    - `GenerateRequest` - Input for solution generation
    - `GenerateResponse` - Output with results and score
    - `TestResult` - Individual test case results
    - `RunSummary` - Brief run information for history

### `storage.py` - Data Persistence

- **Purpose**: Handles JSON file-based storage
- **Key Functions**:
    - `save_run()` - Stores complete run records
    - `list_runs()` - Lists run files (sorted by timestamp)
    - `load_run()` - Retrieves specific run data
- **Storage**: Uses `runs/` directory for JSON files

### Backend Files

#### **Core Application Files (`/backend/app/`)**

##### **`main.py` - FastAPI Application**
- **Purpose**: Main FastAPI server with REST API endpoints
- **Key Features**:
  - CORS middleware for frontend communication
  - `POST /generate_solution` - Generates and tests AI solutions
  - `GET /results/{run_id}` - Retrieves specific run results
  - `GET /runs` - Lists recent runs with summaries
- **Dependencies**: Uses models, agent, and storage modules

##### **`api/` - API Routes**
- **`routes_generate.py`** - Solution generation endpoints
- **`routes_results.py`** - Results and history endpoints

##### **`core/` - Core Business Logic**
- **`agent.py`** - Main orchestration logic for problem solving
- **`llm.py`** - OpenAI integration and code generation
- **`runner.py`** - Safe code execution engine

##### **`models/` - Data Models**
- **`problem.py`** - Pydantic schemas for API requests/responses

##### **`utils/` - Utility Functions**
- **`file_ops.py`** - File operations and JSON persistence

##### **`cli.py` - CLI Interface (Module)**
- **Purpose**: Command-line interface for the agent
- **Features**:
    - Argument parsing for problem and test cases
    - JSON validation for test case format
    - Optional self-reflection with retry limits
    - Detailed output formatting with scores and results
- **Usage**: `python -m app.cli --problem "..." --test-cases '[...]'`

#### **Root Backend Files**

##### **`cli.py` - Standalone CLI Script**
- **Purpose**: Standalone command-line entry point
- **Features**: Same as module CLI but with direct imports
- **Usage**: `python backend/cli.py --problem "..." --test-cases '[...]'`

### `evaluate.py` - Benchmark Evaluation

- **Purpose**: Runs the agent on benchmark problems
- **Features**:
    - Loads test problems from `eval_set.json`
    - Calculates overall performance metrics
    - Saves evaluation results to `runs/eval_history.json`
    - Provides detailed scoring and statistics
- **Usage**: `python backend/evaluate.py`

### `prompt_template.txt` - LLM System Prompt

- **Purpose**: Customizes how the LLM generates code
- **Content**: Instructions for generating Python functions named `solve`
- **Fallback**: Built-in default prompt in `llm.py`

### `requirements.txt` - Python Dependencies

- **Dependencies**:
    - `fastapi` - Web framework
    - `uvicorn[standard]` - ASGI server
    - `openai` - LLM API client
    - `pydantic` - Data validation
    - `python-dotenv` - Environment variable loading
    - `pydantic-settings` - Settings management

### `eval_set.json` - Benchmark Test Cases

- **Purpose**: Collection of coding problems for evaluation
- **Format**: Array of objects with `problem` and `test_cases` fields
- **Content**: Various difficulty levels from basic arithmetic to algorithms

### Data Files (`/backend/runs/`)

### `run_*.json` - Individual Run Records

- **Purpose**: Stores complete execution records
- **Content**: Problem text, generated code, test results, scores, timestamps
- **Naming**: `run_{timestamp}.json`

### `eval_history.json` - Evaluation Results

- **Purpose**: Stores benchmark evaluation outcomes
- **Content**: Overall scores, individual problem results, statistics

---

## Frontend Files (`/frontend/`)

### React Application (`/frontend/src/`)

### `App.tsx` - Main React Component

- **Purpose**: Primary user interface for the code solver
- **Key Features**:
    - **Problem Input**: Textarea for coding problem descriptions
    - **Test Case Input**: JSON format for test cases with validation
    - **Solution Generation**: Calls backend API to generate solutions
    - **Results Display**: Shows generated code, test results, and scores
    - **History Panel**: Displays past runs with scores and timestamps
    - **Error Handling**: User-friendly error messages
- **State Management**: React hooks for form state and results

### `api.ts` - Backend API Client

- **Purpose**: TypeScript interface for backend communication
- **Key Functions**:
    - `generateSolution()` - POST request to generate solutions
    - `getRuns()` - GET request for run history
    - `getResult()` - GET request for specific run details
- **Types**: Defines interfaces for API requests/responses

### `main.tsx` - React Entry Point

- **Purpose**: Renders the React application
- **Features**: Standard React 18 setup with StrictMode

### `App.css` - Main Stylesheet

- **Purpose**: Comprehensive styling for the application
- **Key Features**:
    - **Modern Design**: Gradient backgrounds, card-based layout
    - **Responsive**: Mobile-friendly with media queries
    - **Interactive**: Hover effects, transitions, status indicators
    - **Color Coding**: Green for passed tests, red for failed tests
    - **Typography**: Clean, readable font hierarchy

### `index.css` - Global Styles

- **Purpose**: Base CSS reset and global styles
- **Features**: CSS reset, font family setup, basic layout

### Configuration Files

### `package.json` - Node.js Dependencies

- **Dependencies**:
    - `react` & `react-dom` - UI framework
    - `@vitejs/plugin-react` - Vite React plugin
    - `typescript` - TypeScript support
    - `vite` - Build tool and dev server
- **Scripts**: Development, build, and preview commands

### `vite.config.ts` - Vite Configuration

- **Purpose**: Build tool configuration
- **Key Features**:
    - React plugin with fast refresh
    - Development server on port 5000
    - API proxy to backend (port 8000)
    - Host binding for network access

### `tsconfig.json` - TypeScript Configuration

- **Purpose**: TypeScript compiler settings
- **Features**: Strict type checking, modern ES2020 target, React JSX support

### `index.html` - HTML Entry Point

- **Purpose**: Main HTML document
- **Features**: Basic HTML5 structure with React root element

---

## Root Files

### `README.md` - Project Documentation

- **Purpose**: Comprehensive project documentation
- **Content**:
    - Feature overview and architecture
    - Setup and usage instructions
    - API documentation
    - Security considerations
    - Future enhancement ideas

### `uv.lock` - Python Lock File

- **Purpose**: Exact dependency versions for reproducible builds
- **Tool**: UV package manager lock file

---

# How to run on local

## 1. Set up Python backend

### Step 1: Move into backend

```bash
cd CODESOLVERAGENTTEST1/backend
```

### Step 2: Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Add your OpenAI API key

Create a `.env` file in the `backend/` folder (next to `.env.example`):

```bash
cp .env.example .env
```

Then open `.env` and paste your OpenAI key:

```
OPENAI_API_KEY=sk-xxxxxx
OPENAI_MODEL=gpt-4o-mini

```

Activate it for your terminal:

```bash
export OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d= -f2)

```

---

## 2. Run the API server

From inside `backend/`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

```

You’ll see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000

```

Now open this in your browser:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

This gives you an interactive Swagger UI to test `/generate_solution` and `/results`.

---

## 3. Try solving a problem via API

In the Swagger UI or terminal, run this:

### Using `curl`

```bash
curl -X POST http://127.0.0.1:8000/generate_solution \
  -H 'Content-Type: application/json' \
  -d '{"problem":"Given two numbers, return their sum.","test_cases":[[[1,2],3],[[-1,5],4]]}'

```

You should get a JSON output like:

```json
{
  "id": "1697900000000",
  "solution_code": "def add(a,b): return a+b",
  "results": [
    {"input": "[1,2]", "expected_output": "3", "output": "3", "passed": true},
    {"input": "[-1,5]", "expected_output": "4", "output": "4", "passed": true}
  ],
  "score": 1.0
}

```

---

## 4. Run via CLI

From `backend/`:

```bash
python -m app.cli \
  --problem "Reverse a string" \
  --test-cases '[[["hello"],"olleh"], [["abc"],"cba"]]'

```

You’ll see printed output and a new log in:

```
backend/runs/run_<timestamp>.json

```

---

## 5. Run Evaluation

To test your full eval set:

```bash
python evaluate.py

```

You’ll see results like:

```
Evaluating 1/2: reverse_string — Given a string s, return the reversed string.
   Result: 3/3 passed | score=1.00 | run_id=1729500000000
🏁 Final Eval Score = 1.00 (6/6)

```

---

## 6. Set up Frontend (React + Vite)

### Step 1: Open a new terminal

```bash
cd CODESOLVERAGENTTEST1/frontend

```

### Step 2: Install dependencies

```bash
npm install

```

### Step 3: Run the dev server

```bash
npm run dev

```

You’ll see something like:

```
VITE v5.0.0  ready in 500ms
➜  Local: http://localhost:5173/

```

### Step 4: Open that URL in your browser

Enter:

- Problem: “Given two numbers, return their sum.”
- Test cases: `[[[1,2],3], [[-1,5],4]]`

Then click **Solve & Run** — you’ll see:

- Generated code
- Table of test results
- Score
- History of previous runs

---

##
