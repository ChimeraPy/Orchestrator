from chimerapy_orchestrator.tests.base_test import BaseTest
from chimerapy_orchestrator.monads import Ok, Err, MayBe, some, none
import pytest


class TestResult(BaseTest):
    def test_result_success(self):
        result = Ok(1)
        assert result.unwrap() == 1

    def test_result_no_value(self):
        result = Ok(None)
        assert result.unwrap() is None

    def test_result_error(self):
        result = Err(Exception("Test"))
        with pytest.raises(Exception):
            result.unwrap()

    def test_map_error(self):
        result = Ok(1)
        assert result.map_error(lambda x: x + 1).unwrap() == 1

        error = Err(Exception("Test"))
        with pytest.raises(TypeError):
            error.map_error(lambda x: x + 1).unwrap()

    def test_map(self):
        result = Ok(1)
        assert result.map(lambda x: x + 1).unwrap() == 2

        exception = Exception("Test")

        def error_func(x):
            raise exception

        assert result.map_error(error_func).unwrap()

        with pytest.raises(Exception) as e:
            result.map(error_func).unwrap()
            assert e is exception



