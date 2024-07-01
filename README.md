# Qcall

Qcall is a module for dynamically calling Python functions.

Qcall stands for "quick call".

Here is a simple example:

```python
>>> from qcall import call
>>> call("print", "hello", "world")
hello world
```

The above code is equivalent to the following:
```python
>>> print("hello", "world")
hello world
```

Using Qcall you can invoke any Python function, constructor or method.
Qcall performs automatic module import, parameter rearrangement if needed,
and returns the result of the function call.

Qcall is useful for implementing domain-specific languages, processing
configuration files, and more.


# Installation

Install default version from the [Python Package Index](https://pypi.org/project/qcall/):

```
pip install qcall
```


# Examples

```python
from qcall import call, QCALL_CONTEXT


y_true = [1.0, 0.0]
y_score = [0.8, 0.2]

# no need to import sklearn.metrics
# let's dynamically call the roc_auc_score function:
result = call("sklearn.metrics.roc_auc_score", y_true, y_score)


# the same result using **kwargs:
result = call(
    "sklearn.metrics.roc_auc_score",
    y_score=y_score,
    y_true=y_true
)

result = call(
    "sklearn.metrics.roc_auc_score",
    **{"y_score": y_score, "y_true": y_true}
)

# Positional argument(s) can be passed through **kwards using the '*' key.
# For example, this is useful when the arguments are specified in a YAML file.

result = call(
    "sklearn.metrics.roc_auc_score",
    **{"*": [y_true, y_score]}
)

# IMPORTANT: if the function to be call has only one postional argument,
# and the '*' key contains only a list argument,
# it should be wrapped with another list for correct function call:
def some_function(a):
    print(a)

result = call("some_function", **{'*': [[1, 2, 3]], QCALL_CONTEXT: locals()})
# the above is equalent to: some_function([1, 2, 3])

# an example of calling a built-in function:
max_value = call("max", [1, 3, 5, 7])

# an example of calling a constructor:
classifier = call("sklearn.linear_model.LogisticRegression")

x_train = [[0.0], [1.0]]
y_train = [0.0, 1.0]

# examples of calling methods and using the context parameter:
call("classifier.fit", x_train, y_train, qcall_context=locals())
x_test = [[0.1], [0.9]]
p_test = call("classifier.predict_proba", x_test, qcall_context=locals())
```
