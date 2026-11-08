"""Production REST service of MotionEngine (FastAPI, OpenAPI 3).

    pip install -e ".[api]"
    uvicorn vdsim.service.app:app --host 0.0.0.0 --port 8000      # or: motion-engine-api

Endpoints: /health, /metrics, /vehicle, /trajectory, /simulate, /plan, /predict.
Swagger UI is served at /docs, the OpenAPI 3 description at /openapi.json.

The standard-library server in vdsim.api.server (job queue, batch, sweep, MATLAB) stays
available; this package is the synchronous, schema-validated service for deployment.
"""

from .app import create_app

__all__ = ["create_app"]
