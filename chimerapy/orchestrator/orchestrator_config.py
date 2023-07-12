from functools import lru_cache
from typing import ClassVar, Optional

from pydantic import BaseSettings, Field


class OrchestratorConfig(BaseSettings):
    """The settings for the orchestrator."""

    instance: ClassVar[Optional["OrchestratorConfig"]] = None
    mode: str = "dev"
    cluster_manager_port: int = Field(
        default=5000, description="The port for the cluster manager."
    )

    cluster_manager_logdir: str = Field(
        default="chimerapy_orchestrator_logs",
        description="The logdir for the cluster manager.",
    )

    cluster_manager_max_num_of_workers: int = Field(
        default=50,
        description="The maximum number of workers that can be connected to the cluster manager.",
    )

    num_dev_workers: int = Field(
        default=2,
        description="The number of workers to start in dev mode.",
    )

    def dump_env(self, file=".env"):
        with open(file, "w") as f:
            for field, value in self.dict().items():
                f.write(f"{field.upper()}={value}\n")

    class Config:
        allow_extra = False
        allow_mutation = False
        env_file = ".env"


@lru_cache()
def get_config():
    return OrchestratorConfig()
