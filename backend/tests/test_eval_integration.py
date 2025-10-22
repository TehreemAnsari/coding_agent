import subprocess, os

def test_eval_runs():
    # run evaluate.py from backend/
    here = os.path.dirname(__file__)
    backend_dir = os.path.abspath(os.path.join(here, ".."))
    result = subprocess.run(
        ["python", "evaluate.py"],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )
    # Show stderr if something fails (helps debug in CI)
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)
    assert result.returncode == 0, "evaluate.py failed to run"
    # The script should print the final score to stdout or stderr
    assert ("Final Eval Score" in result.stdout) or ("Final Eval Score" in result.stderr)
