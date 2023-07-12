import pytest


class BaseTest:
    @pytest.fixture
    def initdir(self, tmpdir):
        return tmpdir.chdir()
