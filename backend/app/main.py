from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes_generate import router as generate_router
from .api.routes_results import router as results_router

app = FastAPI(title="CodeSolverAgent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Code-Solver Agent API", "status": "running"}

# Include routers
app.include_router(generate_router)
app.include_router(results_router)
