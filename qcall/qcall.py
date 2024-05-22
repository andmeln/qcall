import builtins
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple


QCALL_CONTEXT = "qcall_context"


def get_object(
    name: str, context: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    """
    Return the object by its name.

    Args:
        name: The name of the object to be returned.
        context: An optional dictionary where keys
            are object names and values are objects.

    Returns:
        The object or None.

    Raises:
        None.

    Notes:
        - The name can be a fully qualified function name, including the module
          name.
        - If a context is provided, the name can be either a key in the context
          dictionary or a key followed by the name of the method/attribute,
          separated by a dot.
    """
    name = str(name)
    if hasattr(builtins, name):
        return getattr(builtins, name)
    if context and name in context:
        return context[name]
    path = name.split(".")
    if context and len(path) == 2:
        obj_name, attr_name = path
        if obj_name in context and hasattr(context[obj_name], attr_name):
            return getattr(context[obj_name], attr_name)
    module_name = ".".join(path[:-1])
    if len(path) == 1:
        try:
            return __import__(name)
        except BaseException:
            pass
    try:
        obj = __import__(module_name)
        for subname in path[1:]:
            if hasattr(obj, subname):
                obj = getattr(obj, subname)
            else:
                return None
        return obj
    except BaseException:
        pass
    return None


def _rearrange_parameters(
    signature: inspect.Signature,
    positional_args: Optional[List[Any]] = None,
    keyword_args: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Move positional parameters from keyword ones.

    Args:
        signature: The function signature.
        positional_args: An optional list of positional arguments.
        keyword_args: An optionad dictionary of keyword arguments.

    Returns:
        A tuple consisting of a list of positional arguments and
        a dictionary of keyword arguments.
    """
    args = positional_args or []
    kwargs = keyword_args or {}
    for param in signature.parameters.values():
        if param.name not in kwargs:
            continue
        if (
            param.kind == inspect.Parameter.POSITIONAL_ONLY
            or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        ):
            args.append(kwargs.pop(param.name))
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            value = kwargs.pop(param.name)
            if isinstance(value, list):
                args.extend(value)
            else:
                args.append(value)
    return (args, kwargs)


def get_parameters(
    callable_obj: Callable,
    positional_args: Optional[List[Any]] = None,
    keyword_args: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Return positional and keyword parameters for the specified
    callable object and arguments.

    Args:
        callable_obj: А function-like object.
        positional_args: Аn optional list of positional arguments.
        keyword_args: Аn optionad dictionary of keyword arguments.

    Returns:
        A tuple consisting of a list of positional arguments and
        a dictionary of keyword arguments.
    """
    args = positional_args or []
    kwargs = keyword_args or {}
    if "*" in kwargs:
        if args:
            raise ValueError(
                "Args and the `*` key in kwargs cannot be "
                "specified at the same time."
            )
        args = kwargs["*"]
        kwargs = {k: kwargs[k] for k in kwargs if k != "*"}
    try:
        signature = inspect.signature(callable_obj)
        args, kwargs = _rearrange_parameters(signature, args, kwargs)
    except BaseException:
        pass
    return args, kwargs


def call(name: str, *args, **kwargs) -> Any:
    """
    Call the function-like object by its name with the specified arguments.

    Args:
        name: The name of the function-like object to be called.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
                  You can pass a call_context parameter to kwargs,
                  which is not passed to the called function,
                  but allows you to specify the names of
                  user objects and their values.

    Returns:
        The result of the function call.

    Raises:
        NameError: Raises an error if the name is not defined in modules or
            the context.
        TypeError: Raises an error if the name is not related to a callable
            object.

    Notes:
        - The name can be a fully qualified function name,
          including the module name. Python built-in functions can be
          specified without a module name.
        - Using using the qcall_context argument you can specify a dictionary
          representing a symbol table. The name can be either a key in the
          context dictionary or a key followed by the name of
          the method/attribute, separated by a dot.
        - Positional argument(s) can be passed through **kwards using
          the '*' key. For example, this is useful when the arguments are
          specified in a YAML file.
    """
    context = kwargs.get(QCALL_CONTEXT, None) or dict()
    kwargs = {k: kwargs[k] for k in kwargs if k != QCALL_CONTEXT}
    obj = get_object(name, context)
    if not obj:
        raise NameError(f"name '{name}' is not defined")
    if not callable(obj):
        raise TypeError(f"'{name}' object is not callable")
    args, kwargs = get_parameters(obj, args, kwargs)
    return obj(*args, **kwargs)
