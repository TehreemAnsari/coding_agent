from fastapi import APIRouter, HTTPException
from ..models.problem import RunSummary
from ..utils.file_ops import list_runs, load_run

router = APIRouter()

@router.get("/results/{run_id}")
def get_result(run_id: str):
    try:
        record = load_run(run_id)
        return record
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs", response_model=list[RunSummary])
def get_runs(limit: int = 20):
    try:
        files = list_runs()[:limit]
        summaries = []
        for fname in files:
            run_id = fname.replace("run_", "").replace(".json", "")
            try:
                record = load_run(run_id)
                problem_preview = record.get("problem_text", "")[:100]
                if len(record.get("problem_text", "")) > 100:
                    problem_preview += "..."
                
                summaries.append(RunSummary(
                    run_id=run_id,
                    timestamp=record.get("timestamp", ""),
                    score=record.get("score", 0.0),
                    problem_preview=problem_preview
                ))
            except Exception:
                continue
        return summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
