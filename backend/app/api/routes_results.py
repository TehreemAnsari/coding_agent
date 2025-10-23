from fastapi import APIRouter, HTTPException, Query
from ..models.problem import RunSummary
from ..utils.file_ops import list_runs, load_run

router = APIRouter()


@router.get("/results/{run_id}")
def get_result(run_id: str):
    """
    Retrieve full result for a specific run (complete JSON log).
    """
    try:
        record = load_run(run_id)
        if not record:
            raise FileNotFoundError
        return record
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs")
def get_runs(limit: int = Query(20, ge=1, le=100), expand: bool = Query(False)):
    """
    List previous runs.
    - By default: returns summaries (run_id, score, timestamp, preview).
    - If expand=true: returns full run logs (includes code, test cases, etc.)
    """
    try:
        files = list_runs()[:limit]
        runs = []
        for fname in files:
            run_id = fname.replace("run_", "").replace(".json", "")
            try:
                record = load_run(run_id)
                if not record:
                    continue

                # Expanded: return full record
                if expand:
                    runs.append(record)
                    continue

                # Summary mode (default)
                problem_preview = record.get("problem_text", "")[:100]
                if len(record.get("problem_text", "")) > 100:
                    problem_preview += "..."

                runs.append(RunSummary(
                    run_id=run_id,
                    timestamp=record.get("timestamp", ""),
                    score=record.get("score", 0.0),
                    problem_preview=problem_preview
                ))
            except Exception:
                continue
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
