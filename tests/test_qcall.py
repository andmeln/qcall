import math
import os.path

import pytest
from qcall import call, get_object, get_parameters, QCALL_CONTEXT


def sample_function_1(a, b, /, foo="foo", *, bar="bar", **kwargs):
    return {"a": a, "b": b, "foo": foo, "bar": bar, "kwargs": kwargs}


def sample_function_2(a, *b, foo="bar", **kwargs):
    return {"a": a, "b": b, "foo": foo, "kwargs": kwargs}


def test_get_object():
    assert get_object("print") == print
    assert get_object("qcall.get_object") == get_object
    assert get_object("os.path") == os.path
    assert get_object("os.path.join") == os.path.join
    assert get_object("math") == math
    assert get_object("math.exp") == math.exp
    assert get_object("math.pi") == math.pi
    assert get_object("math.nonexistent") is None
    assert get_object("nonexistent.foo.bar") is None
    assert get_object("") is None
    assert get_object(None) is None
    context = {"foo": "bar"}
    assert get_object("foo", context) == "bar"
    assert get_object("foo.upper", context)() == "BAR"
    assert get_object("foo.nonexistent", context) is None
    assert get_object("nonexistent", context) is None
    context = {"1": sample_function_1, "2": sample_function_2}
    assert get_object("1", context) == sample_function_1


def test_get_parameters():
    assert get_parameters(print, keyword_args={"*": [123], "sep": ""}) == (
        [123],
        {"sep": ""},
    )
    assert get_parameters(
        sample_function_1, keyword_args={"a": 1, "b": 2, "foo": 3, "bar": 4}
    ) == ([1, 2], {"foo": 3, "bar": 4})
    assert get_parameters(
        sample_function_2, keyword_args={"a": 1, "b": 2, "bar": 3}
    ) == ([1, 2], {"bar": 3})
    assert get_parameters(
        sample_function_2, keyword_args={"a": 1, "b": [2, 3], "bar": 4}
    ) == ([1, 2, 3], {"bar": 4})


def test_call_print():
    assert call("print") is None
    assert call("print", "foo", sep="") is None
    assert call("print", "foo", "bar", sep=",") is None
    assert call("print", **{"*": ["foo", "bar"], "sep": ""}) is None
    assert call("print", **{"*": "foo", "sep": ""}) is None


def test_call_max():
    assert call("max", 1, 2) == 2
    assert call("max", 1, 2, 3) == 3
    assert call("max", [1, 2, 3]) == 3
    assert call("max", **{"*": [1, 2, 3]}) == 3
    assert call("max", **{"*": [3, 5], "key": lambda x: -x}) == 3
    assert call("max", *[3, 5], **{"key": lambda x: -x}) == 3


def test_call_nonexistent_function():
    with pytest.raises(NameError, match=r"foo.nonexistent"):
        call("foo.nonexistent")


def test_call_noncallable():
    with pytest.raises(TypeError, match=r"math.pi"):
        call("math.pi")


def test_call_args_and_star():
    with pytest.raises(
        ValueError, match=r"cannot be specified at the same time"
    ):
        call("print", "foo", **{"*": "bar", "flush": True})


def test_call_using_context():
    context = {"1": sample_function_1, "2": sample_function_2}
    assert call("1", **{"a": 1, "b": 2, "bar": 4, QCALL_CONTEXT: context}) == {
        "a": 1,
        "b": 2,
        "foo": "foo",
        "bar": 4,
        "kwargs": {},
    }
    assert call("2", **{"a": 1, "b": [2, 3], QCALL_CONTEXT: context}) == {
        "a": 1,
        "b": (2, 3),
        "foo": "bar",
        "kwargs": {},
    }


def test_call_dict_get():
    context = {"foo": {"a": 1, "b": 2}}
    assert call("foo.get", "a", qcall_context=context) == 1
    assert call("foo.get", **{"*": "b", QCALL_CONTEXT: context}) == 2
    assert call("foo.get", "c", 3, qcall_context=context) == 3
    assert call("foo.get", "d", None, qcall_context=context) is None
