import asyncio
import concurrent.futures
import signal
from contextlib import asynccontextmanager
from pathlib import Path
from types import FrameType

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import FileResponse, HTMLResponse, Response

from chimerapy_orchestrator.init_services import get, initialize, teardown
from chimerapy_orchestrator.orchestrator_config import get_config
from chimerapy_orchestrator.routers.cluster_router import ClusterRouter
from chimerapy_orchestrator.routers.pipeline_router import PipelineRouter

APP_DESCRIPTION = """
REST API for managing the ChimeraPy cluster.

With this API, any client application can manage the cluster, including:
- Creating and managing pipelines for ChimeraPy
- Managing the cluster itself
- Running pipelines on the cluster

For more information, please visit the [documentation](https://chimerapy.readthedocs.io/en/latest/).
"""

STATIC_FILES_DIR = Path(__file__).parent / "build"


@asynccontextmanager
async def lifespan(app: "Orchestrator"):
    default_sigint_handler = signal.getsignal(signal.SIGINT)
    cluster_service = get("cluster_manager")
    task1 = asyncio.create_task(cluster_service.start_async_tasks())
    await cluster_service.update_network_status()

    def shutdown():
        teardown()
        if not task1.done():
            task1.cancel()

    def shutdown_on_sigint(signum: int, frame: FrameType = None):
        shutdown()
        default_sigint_handler(signum, frame)

    signal.signal(signal.SIGINT, shutdown_on_sigint)
    yield
    shutdown()


class Orchestrator(FastAPI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        cluster_manager = get("cluster_manager")
        pipelines = get("pipelines")
        self.include_router(PipelineRouter(pipelines))
        self.include_router(ClusterRouter(cluster_manager))

        config = get_config()
        if config.mode != "dev":

            if not STATIC_FILES_DIR.exists():
                raise FileNotFoundError(
                    "The build directory does not exist. Please run `cd dashboard` followed "
                    "by `npm run build` to build the frontend from the root directory."
                )

            self.middleware("http")(self.static_middleware)

    async def static_middleware(self, request: Request, call_next) -> Response:
        """Serve the static files from the '/dashboard' path."""
        if request.url.path.startswith("/dashboard"):
            return await self._serve_static_file(request)

        return await call_next(request)

    async def _serve_static_file(self, request: Request) -> Response:
        """Serve the static file from the build directory."""
        path = request.url.path.replace("/dashboard", "")

        if path == "/" or path == "":
            path = "index.html"
            with open(STATIC_FILES_DIR / path) as f:
                return HTMLResponse(f.read())
        else:
            if path.startswith("/"):
                path = path[1:]
            if (pth := (STATIC_FILES_DIR / path)).exists() or (
                pth := (STATIC_FILES_DIR / f"{path.replace('/', '')}.html")
            ).exists():
                return FileResponse(pth)
            else:
                return Response(
                    status_code=404, content=f"{request.url.path} not found"
                )


def create_orchestrator_app() -> "Orchestrator":
    with concurrent.futures.ThreadPoolExecutor() as pool:  # This had to be done because uvicorn blocks the event loop
        pool.submit(initialize)

    orchestrator = Orchestrator(
        title="ChimeraPyOrchestrator",
        lifespan=lifespan,
        description=APP_DESCRIPTION,
        contact={
            "name": "Umesh Timalsina",
            "email": "umesh.timalsina@vanderbilt.edu",
        },
    )
    return orchestrator
