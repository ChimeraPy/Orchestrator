import pytest

from chimerapy.orchestrator.monads import Err, Ok, none, some
from chimerapy.orchestrator.tests.base_test import BaseTest


class TestMonads(BaseTest):
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

    def test_ok(self):
        result = Ok(1)
        assert result.ok().unwrap() == 1

        error = Err(Exception("Test"))
        assert error.ok().unwrap_or(2) == 2

    def test_some(self):
        assert some(1).unwrap() == 1
        assert some(None).unwrap() is None
        assert some(None).is_some()

    def test_none(self):
        assert none().unwrap_or(1) == 1
        assert none().unwrap_or_else(lambda: 1) == 1
        assert none().map(lambda x: x + 1).unwrap_or(1) == 1
        assert none().map_or(1, lambda x: x + 1) == 1
        assert none().is_none()

        with pytest.raises(Exception):
            none().unwrap()
