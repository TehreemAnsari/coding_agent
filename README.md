# Initial Problem: SWE interview task

Build a Mini “Code-Solver Agent” Platform (Frontend + Backend)

## Overview

Build a full-stack coding agent that:

- Accepts a coding problem
- Generates a Python solution
- Runs test cases
- Returns output code and pass score
- Stores logs and results
- Includes a simple chat-like frontend that interacts with the backend API

The **backend** should also support CLI usage for direct testing.

# Backend (Core API + CLI Tool)

### Suggested Tech Stack

- **Python**
- **FastAPI**
- **OpenAI SDK**

The agent should be able to write, read, and execute Python scripts to solve coding problems.

**Core Agent Behavior:**

1. Accept a problem statement and test cases.
2. Generate a Python solution file (`solution.py`).
3. Execute test cases via calls (e.g. `python [solution.py](http://solution.py) --input "[1,2,3]"`). The solution.py should accept the —input and print only the output to stdout. It'll make it easy to run test cases.
4. Compute test results:
    - Total test cases
    - Passed count
    - Score = passed / total
5. Save a detailed JSON log in `runs/run_<timestamp>.json` including:
    - Problem text
    - Generated code
    - Test results
    - Pass rate
    - LLM trajectory / conversation history

**Example Log:**

```json
{
  "run_id": 2,
  "problem_text": "Reverse a string",
  "solution_code": "def reverseString(s): return s[::-1]",
  "test_cases": [
    {
      "input": "['hello']",
      "expected_output": "'olleh'",
      "output": "'olleh'",
      "passed": true
    }
  ],
  "score": 1.0,
  "error": null,
  "llm_trajectory": []
}
```

### 1. CLI Interface

**Example Commands:**

```bash
# Standalone CLI (recommended)
python backend/cli.py \
  --problem "Write a function that returns the sum of two numbers" \
  --test-cases '[[[1, 2], 3], [[10, 20], 30]]'

# Module CLI (alternative)
python -m app.cli \
  --problem "Reverse a string" \
  --test-cases '[[["hello"], "olleh"]]'

# With self-reflection
python backend/cli.py \
  --problem "Your problem here" \
  --test-cases '[[[inputs], expected], ...]' \
  --reflection \
  --retries 2
```

Accept a problem statement (`--problem`) and test cases (`--test-cases` as a JSON string).

### 2. API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/generate_solution` | POST | Solve a problem, run tests, return JSON results. Same as CLI |
| `/results/{id}` | GET | Retrieve previous run logs |

**Example Request (`/generate_solution`):**

```json
{
  "problem": "Given two numbers, return their sum.",
  "test_cases": [[[1,2],3]]
}
```

**Example Response:**

```json
{
  "id": 1,
  "solution_code": "def add(a,b): return a+b",
  "results": [
    {"input": "[1,2]", "expected_output": "3", "output": "3", "passed": true}
  ],
  "score": 1.0,
  "test_cases_generated": false,
  "error": null
}
```

## Test Case Format

Each test case is represented as:

```
[[inputs], expected_output]

[[arg1, arg2, arg3], expected_output]
```

---

## Examples

### 1. Single Input

**Test Case:**

```python
[[["hello"], "olleh"]]
```

**Function Signature:**

```python
def reverseString(s):
    ...
```

**Calls:**

```python
reverseString("hello")
```

---

### 2. Multiple Inputs

**Test Case:**

```python
[[[1, 2], 3], [[-1, 5], 4]]
```

**Function Signature:**

```python
def add(a, b):
    ...
```

**Calls:**

```python
add(1, 2)
add(-1, 5)
```

---

### 3. Array inputs

**Test Case:**

```python
[[[[1,2,3]], 6]]
```

**Function Signature:**

```python
def maxSubArray(arr):
    ...
```

**Calls:**

```python
maxSubArray([1,2,3])
```

# Frontend (Chat UI)

### Suggested Tech Stack

- React (Vite or Next.js) + TailwindCSS
- TypeScript

*(Alternatives stacks are allowed.)*

### Features

1. **Chat Interface**
    - User inputs problem text and test cases.
    - Sends requests and displays real-time chat and execution logs (LLM trajectories).
2. **Result Display**
    - Code block for generated solution.
    - Table: | Input | Output | Expected | Pass |
    - Summary section with pass rate and error messages.
3. **History**
    - Fetch logs via `/results` endpoint.
    - Each log shows timestamp, score, and expandable details.

## Evaluation Set:

[eval_set.json](Problem%20SWE%20interview%20task%2029396a81c0db80cbad8eef72e15229b2/eval_set.json)

This set includes problem with test cases. Run your agent of this set and calculate the final score with

- Score = passed / total(100)

## Evaluation Criteria

| Category | Description |
| --- | --- |
| Functionality | CLI, API, and frontend work correctly |
| Eval Score | Calcuated by running your agent on eval set |
| Code Quality | Readable, modular, and well-documented |
| Architecture | Agent scuffold and other design decision  |

## Deliverables

1. Autonomous agent (problem solver + test runner + scorer)
2. Eval metric calculated on the evaluation set
3. API endpoints and data persistence
4. Frontend chat UI integration
5. A [README.md](http://README.md) with instruction to use and proper code documentation


#################################

# Solution: Code-Solver Agent

A full-stack AI-powered coding problem solver that uses LLMs to generate Python solutions, executes them against test cases, and provides detailed scoring and results.

## Features

- **AI Code Generation**: Uses OpenAI to generate Python solutions from problem descriptions
- **Automated Testing**: Executes generated code against test cases with timeout controls
- **Safe Execution**: Sandboxed subprocess execution with basic security checks
- **JSON Logging**: Stores every run with complete details (problem, code, results, score)
- **Web UI**: React-based chat interface for submitting problems and viewing results
- **CLI Interface**: Command-line tool for running the agent
- **API Endpoints**: FastAPI backend with REST endpoints
- **Run History**: Browse past runs and their results

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

## Enhanced Code Organization

The backend has been restructured for better maintainability and developer experience:

### **Modular Architecture**
- **`api/`** - FastAPI route handlers organized by functionality
- **`core/`** - Core business logic (agent, LLM, code execution)
- **`models/`** - Pydantic data models and schemas
- **`utils/`** - Utility functions for file operations and persistence

### **Enhanced Imports**
The `__init__.py` files have been enhanced to provide convenient imports:

```python
# Clean, convenient imports
from app.core import solve_problem, parse_test_cases, run, call_llm
from app.models import GenerateRequest, GenerateResponse, TestResult, RunSummary
from app.utils import save_run, list_runs, load_run
from app.api import generate_router, results_router
from app import app

# Traditional imports still work (backward compatible)
from app.core.agent import solve_problem
from app.models.problem import GenerateRequest
```

### **Benefits**
- **Better Organization**: Related code grouped together
- **Cleaner Imports**: Shorter, more readable import statements
- **Scalable**: Easy to add new routes, models, or utilities
- **Professional**: Follows modern Python project structure
- **Backward Compatible**: Existing code continues to work

### **Developer Experience**

The enhanced structure provides a better developer experience:

```python
# Import core functionality
from app.core import solve_problem, parse_test_cases

# Import data models
from app.models import GenerateRequest, GenerateResponse

# Import utilities
from app.utils import save_run, load_run

# Import API routers
from app.api import generate_router, results_router

# Import main app
from app import app
```

**Benefits for Developers:**
- **Intuitive Imports**: Clear, logical import paths
- **IDE Support**: Better autocomplete and navigation
- **Modular Development**: Work on specific areas independently
- **Easy Testing**: Import specific functions for unit tests
- **Documentation**: Each module has clear purpose and documentation

### **Code Cleanup**

The repository has been cleaned up to remove redundant files:
- **Removed**: Duplicate CLI files (kept standalone version)
- **Removed**: Test run data files (regenerated as needed)
- **Enhanced**: All `__init__.py` files with proper documentation
- **Organized**: Clear separation of concerns across modules

## Setup

1. **Environment Variables**: Open AI secret

2. **Install Dependencies**: requirement.txt

3. **Run the Application**: (See below for how to run on local)

# Explaination of what all the files do 
(this is what I updated on 21st Oct, new files may be added in future)

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

## System Architecture

### Data Flow

1. **User Input** → Frontend form submission
2. **API Request** → FastAPI backend receives problem + test cases
3. **LLM Generation** → OpenAI generates Python solution
4. **Code Execution** → Safe subprocess execution with timeout
5. **Result Processing** → Test case validation and scoring
6. **Storage** → JSON file persistence
7. **Response** → Results returned to frontend
8. **Display** → User sees code, results, and score

### Security Features

- **Code Sandboxing**: Import restrictions and pattern blocking
- **Timeout Controls**: Prevents infinite loops
- **Input Validation**: JSON schema validation
- **Error Handling**: Graceful failure modes

### Technologies Used

- **Backend**: FastAPI, OpenAI API, Python subprocess
- **Frontend**: React, TypeScript, Vite
- **AI**: OpenAI GPT models
- **Storage**: JSON file-based persistence
- **Security**: Static analysis and runtime restrictions

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
