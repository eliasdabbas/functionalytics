import logging
import re

import pytest
from functionalytics.log_this import log_this


@pytest.fixture(autouse=True)
def reset_logging(monkeypatch):
    # Reset logging handlers before each test to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    yield


def read_log_file(log_path):
    with open(log_path, "r") as f:
        return f.read()


def test_basic_logging_to_stderr(caplog):
    @log_this()
    def add(a, b):
        return a + b

    with caplog.at_level(logging.INFO):
        result = add(1, 2)
    assert result == 3
    assert any("Calling: " in record for record in caplog.text.splitlines())
    assert "Args: [1, 2]" in caplog.text
    assert "Kwargs: {}" in caplog.text
    assert "Attrs: {}" in caplog.text


def test_logging_to_file(tmp_path):
    log_file = tmp_path / "test.log"

    @log_this(file_path=str(log_file))
    def mul(a, b):
        return a * b

    mul(2, 5)
    log_content = read_log_file(log_file)
    assert "Calling: " in log_content
    assert "Args: [2, 5]" in log_content


def test_log_format(tmp_path):
    log_file = tmp_path / "test_format.log"
    fmt = "{levelname}:{message}"

    @log_this(file_path=str(log_file), log_format=fmt)
    def foo(x):
        return x

    foo(42)
    log_content = read_log_file(log_file)
    assert log_content.startswith("INFO:")


def test_discard_params(caplog):
    @log_this(discard_params={"secret"})
    def f(a, secret, b=10):
        return a + b

    with caplog.at_level(logging.INFO):
        f(1, "topsecret", b=3)
    assert "secret" not in caplog.text
    assert "Args: [1]" in caplog.text
    assert "Kwargs: {'b': 3}" in caplog.text


def test_param_attrs(caplog):
    @log_this(param_attrs={"payload": len}, discard_params={"payload"})
    def send(payload: bytes):
        return payload

    data = b"123456"
    with caplog.at_level(logging.INFO):
        send(data)
    assert "Attrs: {'payload': 6}" in caplog.text
    assert "payload" not in caplog.text or "b'123456'" not in caplog.text


def test_param_attrs_transform_error(caplog):
    def fail(x):
        raise ValueError("fail!")

    @log_this(param_attrs={"x": fail})
    def foo(x):
        return x

    with caplog.at_level(logging.INFO):
        foo(123)
    assert "<transform error: " in caplog.text


def test_kwargs_and_args(caplog):
    @log_this()
    def f(a, b, c=3):
        return a + b + c

    with caplog.at_level(logging.INFO):
        f(1, 2, c=4)
    assert "Args: [1, 2]" in caplog.text
    assert "Kwargs: {'c': 4}" in caplog.text


def test_multiple_calls(caplog):
    @log_this()
    def inc(x):
        return x + 1

    with caplog.at_level(logging.INFO):
        inc(1)
        inc(2)
    assert caplog.text.count("Calling:") == 2


def test_logger_name_in_log(caplog):
    @log_this()
    def foo(x):
        return x

    with caplog.at_level(logging.INFO):
        foo(1)
    # Should include module and qualname
    assert re.search(r"Calling: [\w\.\<\>]+foo", caplog.text)


def test_discard_and_param_attrs_overlap(caplog):
    @log_this(param_attrs={"token": lambda t: t[:3]}, discard_params={"token"})
    def f(token):
        return token

    with caplog.at_level(logging.INFO):
        f("abcdef")
    assert "Attrs: {'token': 'abc'}" in caplog.text
    assert "abcdef" not in caplog.text or "token" not in caplog.text


def test_default_values(caplog):
    @log_this()
    def f(a, b=5):
        return a + b

    with caplog.at_level(logging.INFO):
        f(10)
    assert "Args: [10]" in caplog.text
    assert "Kwargs: {'b': 5}" in caplog.text or "Kwargs: {}" in caplog.text


def test_python310_utc(monkeypatch, caplog):
    # Simulate Python <3.11 (no datetime.UTC)
    monkeypatch.delattr("datetime.UTC", raising=False)

    @log_this()
    def foo(x):
        return x

    with caplog.at_level(logging.INFO):
        foo(1)
    assert "Calling: " in caplog.text


def test_extra_data_logging(caplog):
    @log_this(extra_data={"key1": "val1", "key2": 123})
    def add(a, b):
        return a + b

    with caplog.at_level(logging.INFO):
        add(1, 2)
    assert "Extra: {'key1': 'val1', 'key2': 123}" in caplog.text


def test_extra_data_empty_or_none(caplog):
    @log_this(extra_data={})
    def func_empty_extra(a):
        return a

    with caplog.at_level(logging.INFO):
        func_empty_extra(1)
    assert "Extra:" not in caplog.text

    @log_this(extra_data=None)
    def func_none_extra(a):
        return a

    with caplog.at_level(logging.INFO):
        func_none_extra(1)
    assert "Extra:" not in caplog.text

    @log_this()
    def func_default_extra(a):
        return a

    with caplog.at_level(logging.INFO):
        func_default_extra(1)
    assert "Extra:" not in caplog.text


def test_extra_data_with_other_params(caplog):
    @log_this(param_attrs={"a": str}, discard_params={"b"}, extra_data={"user": "test"})
    def func(a, b):
        return a, b

    with caplog.at_level(logging.INFO):
        func(10, "secret")

    assert "Attrs: {'a': '10'}" in caplog.text
    assert "'secret'" not in caplog.text  # Checking if 'secret' value is logged
    assert "Args: [10]" in caplog.text  # Make sure 'b' is not in Args
    assert "Kwargs: {}" in caplog.text  # Make sure 'b' is not in Kwargs
    assert "Extra: {'user': 'test'}" in caplog.text


def test_error_logging_to_file(tmp_path):
    log_file = tmp_path / "test.log"
    error_file = tmp_path / "error.log"

    @log_this(file_path=str(log_file), error_file_path=str(error_file))
    def fail_func(x):
        raise ValueError(f"fail: {x}")

    # The function should raise, and error should be logged to error_file
    with pytest.raises(ValueError):
        fail_func(123)
    error_content = read_log_file(error_file)
    assert "Error in" in error_content
    assert "fail: 123" in error_content
    assert "Exception:" in error_content


def test_error_logging_to_stderr(caplog):
    @log_this()
    def fail_func(x):
        raise RuntimeError(f"bad: {x}")

    with pytest.raises(RuntimeError):
        fail_func("oops")
    assert "Error in" in caplog.text
    assert "bad: oops" in caplog.text
    assert "Exception:" in caplog.text
