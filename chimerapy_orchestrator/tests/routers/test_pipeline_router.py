import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chimerapy_orchestrator.pipeline_service.pipelines import Pipelines
from chimerapy_orchestrator.routers.pipeline_router import PipelineRouter
from chimerapy_orchestrator.tests.base_test import BaseTest


class TestPipelineRouter(BaseTest):
    @pytest.fixture(scope="class")
    def pipeline_client(self):
        app = FastAPI()
        app.include_router(PipelineRouter(Pipelines()))
        yield TestClient(app)

    def test_get_pipelines(self, pipeline_client):
        response = pipeline_client.get("/pipeline/list")
        assert response.status_code == 200
        assert response.json() == []
