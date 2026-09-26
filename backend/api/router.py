"""
DevTwin API router — analysis endpoints.
"""
import asyncio
import uuid
from typing import Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from models.analysis import (
    AnalysisRequest, AnalysisStatusResponse, AnalysisStatus, AnalysisResult
)

router = APIRouter()

# In-memory job store (sufficient for prototype)
_jobs: Dict[str, AnalysisStatusResponse] = {}

# Embed the demo diff inline so it works on Vercel serverless (no filesystem access)
_DEMO_DIFF = """\
--- a/services/order_service.py
+++ b/services/order_service.py
@@ -44,8 +44,10 @@ class OrderService:
 
     def update_order(self, user: User, order_id: str, request: UpdateOrderRequest) -> Order:
         order = self._repo.get(order_id)
 
         if not can_modify_order(user, order):
             raise PermissionError("You do not have permission to modify this order")
 
-        if not order.can_be_updated():
-            raise OrderValidationError(
-                f"Order in status '{order.status.value}' cannot be updated"
-            )
+        # Allow updates on both pending and confirmed orders to support
+        # last-minute item corrections before shipping
+        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
+            raise OrderValidationError(
+                f"Order in status '{order.status.value}' cannot be updated"
+            )
"""


def _is_demo_mode() -> bool:
    import os
    return not bool(os.environ.get("GEMINI_API_KEY", "").strip())


@router.get("/projects")
def list_projects():
    """Return available demo projects."""
    return {
        "projects": [
            {
                "id": "demo_orders",
                "name": "Demo Orders",
                "description": "E-commerce order management service",
                "path": "sample_project",
                "language": "Python",
                "files": 7,
            }
        ],
        "demo_mode": _is_demo_mode(),
    }


@router.get("/projects/{project_id}/change")
def get_demo_change(project_id: str):
    """Return the prepared demo change for a project."""
    if project_id != "demo_orders":
        raise HTTPException(status_code=404, detail="Project not found")

    # Try reading from filesystem first (local dev), fall back to embedded (Vercel)
    import os
    diff_text = _DEMO_DIFF
    diff_path = os.path.normpath(os.path.join(
        os.path.dirname(__file__), "..", "..", "sample_project", "demo_change.diff"
    ))
    try:
        with open(diff_path) as f:
            diff_text = f.read()
    except (FileNotFoundError, OSError):
        pass  # use embedded _DEMO_DIFF

    return {
        "project_id": project_id,
        "description": "Allow customers to update orders in CONFIRMED status",
        "diff": diff_text,
        "changed_files": ["services/order_service.py"],
    }


@router.post("/analyze")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start an analysis job and return an ID for polling."""
    analysis_id = str(uuid.uuid4())
    job = AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.PENDING,
        progress_steps=[],
    )
    _jobs[analysis_id] = job
    background_tasks.add_task(_run_analysis, analysis_id, request)
    return {"analysis_id": analysis_id}


@router.get("/analyze/{analysis_id}", response_model=AnalysisStatusResponse)
def get_analysis_status(analysis_id: str):
    """Poll analysis job status."""
    job = _jobs.get(analysis_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return job


async def _run_analysis(analysis_id: str, request: AnalysisRequest):
    """Background task: runs the full agentic workflow."""
    from agents.orchestrator import Orchestrator
    job = _jobs[analysis_id]
    job.status = AnalysisStatus.RUNNING
    try:
        orchestrator = Orchestrator(analysis_id=analysis_id, job=job)
        result = await orchestrator.run(request)
        job.result = result
        job.status = AnalysisStatus.COMPLETE
    except Exception as exc:
        job.status = AnalysisStatus.FAILED
        job.error = str(exc)
        raise
