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
    assert "Values: {'a': 1, 'b': 2}" in caplog.text
    assert "Attrs: {}" in caplog.text


def test_logging_to_file(tmp_path):
    log_file = tmp_path / "test.log"

    @log_this(file_path=str(log_file))
    def mul(a, b):
        return a * b

    mul(2, 5)
    log_content = read_log_file(log_file)
    assert "Calling: " in log_content
    assert "Values: {'a': 2, 'b': 5}" in log_content


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
    assert "'secret': 'discarded'" in caplog.text
    assert "Values: {'a': 1, 'secret': 'discarded', 'b': 3}" in caplog.text


def test_param_attrs(caplog):
    @log_this(param_attrs={"payload": len}, discard_params={"payload"})
    def send(payload: bytes):
        return payload

    data = b"123456"
    with caplog.at_level(logging.INFO):
        send(data)
    assert "Attrs: {'payload': 6}" in caplog.text
    assert "'payload': 'discarded'" in caplog.text


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
    assert "Values: {'a': 1, 'b': 2, 'c': 4}" in caplog.text


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
    assert "'token': 'discarded'" in caplog.text


def test_default_values(caplog):
    @log_this()
    def f(a, b=5):
        return a + b

    with caplog.at_level(logging.INFO):
        f(10)
    assert "Values: {'a': 10, 'b': 5}" in caplog.text


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
    assert "Extra: {}" in caplog.text

    @log_this(extra_data=None)
    def func_none_extra(a):
        return a

    with caplog.at_level(logging.INFO):
        func_none_extra(1)
    assert "Extra: {}" in caplog.text

    @log_this()
    def func_default_extra(a):
        return a

    with caplog.at_level(logging.INFO):
        func_default_extra(1)
    assert "Extra: {}" in caplog.text


def test_extra_data_with_other_params(caplog):
    @log_this(param_attrs={"a": str}, discard_params={"b"}, extra_data={"user": "test"})
    def func(a, b):
        return a, b

    with caplog.at_level(logging.INFO):
        func(10, "secret")

    assert "Attrs: {'a': '10'}" in caplog.text
    assert "'secret'" not in caplog.text  # Checking if 'secret' value is logged
    assert "Values: {'a': 10, 'b': 'discarded'}" in caplog.text  # b should show as discarded
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


def test_error_logging_to_stderr(capsys):
    @log_this()
    def fail_func(x):
        raise RuntimeError(f"bad: {x}")

    with pytest.raises(RuntimeError):
        fail_func("oops")
    captured = capsys.readouterr()
    assert "Error in" in captured.err
    assert "bad: oops" in captured.err
    assert "Exception:" in captured.err


# Tests for log_conditions


def test_log_conditions_none_logs_always(caplog):
    @log_this(log_conditions=None)
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    assert "Calling: " in caplog.text
    assert "Values: {'a': 1}" in caplog.text


def test_log_conditions_empty_dict_logs_always(caplog):
    @log_this(log_conditions={})
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    assert "Calling: " in caplog.text
    assert "Values: {'a': 1}" in caplog.text


def test_log_conditions_single_true_logs(caplog):
    @log_this(log_conditions={"a": lambda x: x > 0})
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    assert "Calling: " in caplog.text
    assert "Values: {'a': 1}" in caplog.text


def test_log_conditions_single_false_no_log(caplog):
    @log_this(log_conditions={"a": lambda x: x < 0})
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    assert "Calling: " not in caplog.text


def test_log_conditions_multiple_true_logs(caplog):
    @log_this(log_conditions={"a": lambda x: x > 0, "b": lambda x: isinstance(x, str)})
    def func(a, b):
        return a, b

    with caplog.at_level(logging.INFO):
        func(1, "hello")
    assert "Calling: " in caplog.text
    assert "Values: {'a': 1, 'b': 'hello'}" in caplog.text


def test_log_conditions_multiple_one_false_no_log(caplog):
    @log_this(log_conditions={"a": lambda x: x < 0, "b": lambda x: isinstance(x, str)})
    def func(a, b):
        return a, b

    with caplog.at_level(logging.INFO):
        func(1, "hello")  # a < 0 is False
    assert "Calling: " not in caplog.text


def test_log_conditions_multiple_all_false_no_log(caplog):
    @log_this(log_conditions={"a": lambda x: x < 0, "b": lambda x: isinstance(x, int)})
    def func(a, b):
        return a, b

    with caplog.at_level(logging.INFO):
        func(1, "hello")  # both False
    assert "Calling: " not in caplog.text


def test_log_conditions_default_param_value_logs(caplog):
    @log_this(log_conditions={"b": lambda x: x == 10})
    def func(a, b=10):
        return a + b

    with caplog.at_level(logging.INFO):
        func(1)  # b should be its default value 10
    assert "Calling: " in caplog.text
    assert "Values: {'a': 1, 'b': 10}" in caplog.text


# Error Handling for log_conditions
def test_log_conditions_raises_key_error_for_invalid_param():
    @log_this(log_conditions={"non_existent": lambda x: True})
    def func(a):
        return a

    with pytest.raises(KeyError) as excinfo:
        func(1)
    assert "Parameter 'non_existent' referenced in log_conditions" in str(excinfo.value)
    assert "is not a valid parameter for function 'func'" in str(excinfo.value)


def test_log_conditions_raises_runtime_error_for_condition_exception():
    def failing_condition(x):
        raise ValueError("Condition failed!")

    @log_this(log_conditions={"a": failing_condition})
    def func(a):
        return a

    with pytest.raises(RuntimeError) as excinfo:
        func(1)
    assert "Error evaluating a condition function within log_conditions" in str(
        excinfo.value
    )
    assert "Condition failed!" in str(
        excinfo.value
    )  # Check original error message is present
    assert isinstance(excinfo.value.__cause__, ValueError)


# Interaction with Other Decorator Features
def test_log_conditions_met_with_other_features(caplog):
    @log_this(
        log_conditions={"a": lambda x: x > 0},
        param_attrs={"b": str},
        discard_params={"c"},
        extra_data={"source": "test"},
    )
    def func(a, b, c):
        return a, b, c

    with caplog.at_level(logging.INFO):
        func(1, 123, "secret")
    assert "Calling: " in caplog.text
    assert "Values: {'a': 1, 'b': 123, 'c': 'discarded'}" in caplog.text  # c shows as discarded
    assert "Attrs: {'b': '123'}" in caplog.text
    assert "Extra: {'source': 'test'}" in caplog.text
    assert "secret" not in caplog.text


def test_log_conditions_not_met_with_other_features_no_log(caplog):
    @log_this(
        log_conditions={"a": lambda x: x < 0},  # This will be False
        param_attrs={"b": str},
        discard_params={"c"},
        extra_data={"source": "test"},
    )
    def func(a, b, c):
        return a, b, c

    with caplog.at_level(logging.INFO):
        func(1, 123, "secret")
    assert "Calling: " not in caplog.text


def test_param_attrs_invalid_parameter():
    """Test that param_attrs raises KeyError for invalid parameter names."""

    @log_this(param_attrs={"non_existent": lambda x: x})
    def func(a):
        return a

    with pytest.raises(KeyError) as excinfo:
        func(1)
    assert "Parameter 'non_existent' referenced in param_attrs" in str(excinfo.value)
    assert "is not a valid parameter for function 'func'" in str(excinfo.value)


# Tests for callable extra_data functionality


def test_extra_data_callable_basic(caplog):
    """Test basic callable extra_data functionality."""

    def get_extra_data():
        return {"timestamp": "2025-05-30", "user_id": 123}

    @log_this(extra_data=get_extra_data)
    def add(a, b):
        return a + b

    with caplog.at_level(logging.INFO):
        add(1, 2)
    assert "Extra: {'timestamp': '2025-05-30', 'user_id': 123}" in caplog.text


def test_extra_data_callable_dynamic(caplog):
    """Test that callable extra_data is called each time and returns different values."""
    call_count = 0

    def get_dynamic_extra_data():
        nonlocal call_count
        call_count += 1
        return {"call_number": call_count}

    @log_this(extra_data=get_dynamic_extra_data)
    def increment(x):
        return x + 1

    with caplog.at_level(logging.INFO):
        increment(100)
        increment(200)

    logs = caplog.text
    assert "Extra: {'call_number': 1}" in logs
    assert "Extra: {'call_number': 2}" in logs


def test_extra_data_callable_empty_dict(caplog):
    """Test callable extra_data that returns empty dict."""

    def get_empty_extra_data():
        return {}

    @log_this(extra_data=get_empty_extra_data)
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    # Empty extra_data should still appear in log as "Extra: {}"
    assert "Extra: {}" in caplog.text


def test_extra_data_callable_with_context(caplog):
    """Test callable extra_data that uses external context."""
    current_user = "test_user"
    session_id = "session_123"

    def get_context_extra_data():
        return {"user": current_user, "session": session_id}

    @log_this(extra_data=get_context_extra_data)
    def process_data(data):
        return data.upper()

    with caplog.at_level(logging.INFO):
        process_data("hello")
    assert "Extra: {'user': 'test_user', 'session': 'session_123'}" in caplog.text


def test_extra_data_callable_exception_handling(caplog):
    """Test that exceptions in callable extra_data are handled gracefully."""

    def failing_extra_data():
        raise ValueError("Something went wrong!")

    @log_this(extra_data=failing_extra_data)
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    assert "Extra: {'<extra_data_error>': 'Something went wrong!'}" in caplog.text


def test_extra_data_callable_complex_data(caplog):
    """Test callable extra_data with complex data types."""

    def get_complex_extra_data():
        return {
            "metadata": {"version": "1.0", "env": "test"},
            "flags": [True, False, True],
            "count": 42,
        }

    @log_this(extra_data=get_complex_extra_data)
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    assert (
        "Extra: {'metadata': {'version': '1.0', 'env': 'test'}, "
        "'flags': [True, False, True], 'count': 42}"
    ) in caplog.text


def test_extra_data_callable_with_param_attrs_and_discard(caplog):
    """Test callable extra_data works with param_attrs and discard_params."""

    def get_extra_data():
        return {"source": "callable", "status": "active"}

    @log_this(
        extra_data=get_extra_data, param_attrs={"data": len}, discard_params={"secret"}
    )
    def process(data, secret):
        return data

    with caplog.at_level(logging.INFO):
        process("hello world", "top_secret")

    log_text = caplog.text
    assert "Values: {'data': 'hello world', 'secret': 'discarded'}" in log_text
    assert "Attrs: {'data': 11}" in log_text
    assert "Extra: {'source': 'callable', 'status': 'active'}" in log_text


def test_extra_data_callable_with_log_conditions(caplog):
    """Test callable extra_data with log_conditions."""

    def get_extra_data():
        return {"conditional_data": "present"}

    @log_this(extra_data=get_extra_data, log_conditions={"value": lambda x: x > 0})
    def func(value):
        return value

    # Should log when condition is met
    with caplog.at_level(logging.INFO):
        func(5)
    assert "Extra: {'conditional_data': 'present'}" in caplog.text

    # Should not log when condition is not met
    caplog.clear()
    with caplog.at_level(logging.INFO):
        func(-1)
    # No logging should occur at all when condition is not met
    assert caplog.text == ""
    assert len(caplog.records) == 0


def test_extra_data_callable_vs_static(caplog):
    """Test that we can distinguish between callable and static extra_data."""

    # Static extra_data
    @log_this(extra_data={"type": "static"})
    def func_static(a):
        return a

    # Callable extra_data
    def get_callable_data():
        return {"type": "callable"}

    @log_this(extra_data=get_callable_data)
    def func_callable(a):
        return a

    with caplog.at_level(logging.INFO):
        func_static(1)
        func_callable(2)

    logs = caplog.text
    assert "Extra: {'type': 'static'}" in logs
    assert "Extra: {'type': 'callable'}" in logs


def test_extra_data_callable_lambda(caplog):
    """Test callable extra_data using lambda functions."""

    @log_this(extra_data=lambda: {"lambda_data": "works"})
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    assert "Extra: {'lambda_data': 'works'}" in caplog.text


def test_extra_data_callable_closure(caplog):
    """Test callable extra_data using closure to capture state."""
    counter = 0

    def make_extra_data_func():
        def get_extra_data():
            nonlocal counter
            counter += 1
            return {"execution_count": counter}

        return get_extra_data

    extra_data_func = make_extra_data_func()

    @log_this(extra_data=extra_data_func)
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
        func(2)

    logs = caplog.text
    assert "Extra: {'execution_count': 1}" in logs
    assert "Extra: {'execution_count': 2}" in logs


def test_extra_data_callable_exception_types(caplog):
    """Test different types of exceptions in callable extra_data."""

    def runtime_error_extra_data():
        raise RuntimeError("Runtime error occurred")

    def type_error_extra_data():
        raise TypeError("Type error occurred")

    @log_this(extra_data=runtime_error_extra_data)
    def func1(a):
        return a

    @log_this(extra_data=type_error_extra_data)
    def func2(a):
        return a

    with caplog.at_level(logging.INFO):
        func1(1)
        func2(2)

    logs = caplog.text
    assert "Extra: {'<extra_data_error>': 'Runtime error occurred'}" in logs
    assert "Extra: {'<extra_data_error>': 'Type error occurred'}" in logs


def test_extra_data_callable_returns_none(caplog):
    """Test callable extra_data that returns None."""

    def get_none_extra_data():
        return None

    @log_this(extra_data=get_none_extra_data)
    def func(a):
        return a

    with caplog.at_level(logging.INFO):
        func(1)
    # None returned by callable should be logged as "Extra: None"
    assert "Extra: {}" in caplog.text


def test_extra_data_callable_preserves_function_return_value(caplog):
    """Test that callable extra_data doesn't overwrite the original function's return value."""
    
    def get_extra_data():
        return {1: "one", 2: "two"}
    
    @log_this(extra_data=get_extra_data)
    def func_returning_list(x):
        return [1, 2, 3, x]
    
    @log_this(extra_data=get_extra_data)
    def func_returning_dict(x):
        return {"original": x, "processed": x * 2}
    
    with caplog.at_level(logging.INFO):
        result_list = func_returning_list(4)
        result_dict = func_returning_dict(5)
    
    # Verify the original function's return values are preserved
    assert result_list == [1, 2, 3, 4]
    assert result_dict == {"original": 5, "processed": 10}
    
    # Verify extra_data is still logged correctly
    assert "Extra: {1: 'one', 2: 'two'}" in caplog.text
