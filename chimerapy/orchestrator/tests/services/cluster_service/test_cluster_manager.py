import asyncio

import pytest

import chimerapy.engine as cpe
from chimerapy.engine.utils import get_ip_address
from chimerapy.orchestrator.models.cluster_models import (
    UpdateMessage,
    UpdateMessageType,
)
from chimerapy.orchestrator.services.cluster_service import ClusterManager
from chimerapy.orchestrator.services.pipeline_service import Pipelines
from chimerapy.orchestrator.tests.base_test import BaseTest

MINUTE = 60


@pytest.mark.slow
class TestClusterManager(BaseTest):
    @pytest.fixture(scope="class")
    def anyio_backend(self):
        return "asyncio"

    @pytest.fixture(scope="class")
    def pipelines(self):
        return Pipelines()

    @pytest.fixture(scope="class")
    def cluster_manager(self, pipelines):
        manager = ClusterManager(
            pipeline_service=pipelines,
            logdir="./logs",
            port=0,
        )
        return manager

    @pytest.fixture(scope="class")
    def pipeline_test(self, pipelines, dev_worker):
        pipeline = pipelines.create_pipeline(
            name="test_pipeline",
            description="test_description",
        ).unwrap()

        screen = pipeline.add_node(node_name="ScreenCaptureNode")
        show = pipeline.add_node("ShowWindow")
        screen.worker_id = dev_worker.id
        show.worker_id = dev_worker.id

        pipeline.add_edge(
            source=screen.id,
            sink=show.id,
        )

        return pipeline

    @pytest.fixture(scope="class")
    def dev_worker(self, cluster_manager):
        worker = cpe.Worker(name="worker1", id="worker1")

        # Add worker to cluster manager
        worker.connect(host=cluster_manager.host, port=cluster_manager.port)

        yield worker
        worker.shutdown()

    def test_get_network(self, cluster_manager):
        assert cluster_manager.get_network().map(
            lambda n: n.to_dict()
        ).unwrap() == {
            "id": cluster_manager._manager.state.id,  # pylint: disable=protected-access
            "workers": {},
            "ip": get_ip_address(),
            "port": cluster_manager._manager.port,  # pylint: disable=protected-access
            "logs_subscription_port": None,
            "log_sink_enabled": True,
            "logdir": str(
                cluster_manager._manager.logdir
            ),  # pylint: disable=protected-access
        }

    @pytest.mark.timeout(30)
    @pytest.mark.anyio
    async def test_network_updates(self, cluster_manager, anyio_backend):
        client_queue = asyncio.Queue()
        asyncio.create_task(cluster_manager.start_async_tasks())

        await cluster_manager.subscribe_to_network_updates(
            client_queue,
            UpdateMessage(
                data=None,
                signal=UpdateMessageType.NETWORK_UPDATE,
            ),
        )

        assert client_queue.qsize() == 1
        msg = await client_queue.get()
        assert msg["signal"] == UpdateMessageType.NETWORK_UPDATE
        assert msg["data"] is None

    @pytest.mark.anyio
    async def test_zeroconf(self, cluster_manager):
        assert cluster_manager.is_zeroconf_discovery_enabled() is False
        cluster_manager.enable_zeroconf_discovery()
        assert cluster_manager.is_zeroconf_discovery_enabled() is True
        cluster_manager.disable_zeroconf_discovery()
        assert cluster_manager.is_zeroconf_discovery_enabled() is False

    @pytest.mark.anyio
    @pytest.mark.timeout(5 * MINUTE)
    async def test_pipeline_operations(self, cluster_manager, pipeline_test):
        # instantiate pipeline
        instance_result = await cluster_manager.instantiate_pipeline(
            pipeline_test.id
        )
        assert instance_result.ok().is_some()
        assert cluster_manager._active_pipeline is pipeline_test
        assert pipeline_test.instantiated
        assert cluster_manager.current_state.name == "INSTANTIATED"

        # commit pipeline
        commit_result = await cluster_manager.commit_pipeline()
        assert commit_result.ok().is_some()
        await asyncio.sleep(20)  # 20 Seconds to commit
        assert pipeline_test.committed
        assert cluster_manager.current_state.name == "COMMITTED"

        # Preview pipeline
        preview_result = await cluster_manager.preview_pipeline()
        await asyncio.sleep(2)  # 5 Seconds to preview
        assert preview_result.ok().is_some()
        assert cluster_manager.current_state.name == "PREVIEWING"

        # Record pipeline
        record_result = await cluster_manager.record_pipeline()
        await asyncio.sleep(10)  # 10 Seconds to record
        assert record_result.ok().is_some()
        assert cluster_manager.current_state.name == "RECORDING"

        # Stop and Back to preview
        stop_result = await cluster_manager.stop_pipeline()
        await asyncio.sleep(5)  # 5 Seconds to stop
        assert stop_result.ok().is_some()
        assert cluster_manager.current_state.name == "STOPPED"

        collect_result = await cluster_manager.collect_pipeline()
        await asyncio.sleep(10)  # 10 Second to collect
        assert collect_result.ok().is_some()
        assert cluster_manager.current_state.name == "COLLECTED"

        preview_result = await cluster_manager.preview_pipeline()
        await asyncio.sleep(5)  # 5 Seconds to preview
        assert preview_result.ok().is_some()
        assert cluster_manager.current_state.name == "PREVIEWING"

        # Reset pipeline
        reset_result = await cluster_manager.reset_pipeline()
        await asyncio.sleep(20)  # 20 Seconds to reset
        assert reset_result.ok().is_some()
        assert cluster_manager.current_state.name == "INITIALIZED"
        assert cluster_manager._active_pipeline is None
        assert not pipeline_test.instantiated
        assert not pipeline_test.committed
