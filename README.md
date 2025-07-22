# `functionalytics`: Effortless Analytics for Your Python Functions

> ⚠️ This package is under development, and semi-stable. Expect some changes but not major ones, and feel free to submit any suggestions or bugs.

functionalytics helps you understand how your users interact with your application, without extra code or complex analytics tools. Just add a decorator to your functions, and log every call, argument, and key attribute for later analysis.

## Why use functionalytics?

- Know your users: See which options, features, or inputs are most popular in your app.
- No hassle: Add a single decorator, no need to rewrite your functions or add tracking code everywhere.
- Stay in control: Choose what gets logged, redact sensitive data, and summarize large inputs.
- Analyze easily: Logs are structured for easy parsing and analysis.

## The name

- `functionalytics`: Rhymes with "functionality"
- Function analytics: Run analytics for your function calls in your apps
- Functional: Use functional programming to implement this through a simple decorator

## The idea

You have an interactive app, and you want to know how many people use which option:

- In a country dropdown, which are the most popular countries?
- How many people enable the "color" checkbox when they create a chart?
- Are people even using the slider we worked so hard to implement?
- Are there any performance difference between the different options selected?

These are some example questions that this package aims to help answer

## Installation

```bash
python3 -m pip install functionalytics
```

## The approach: function decorator + logging (automated)

```python
from functionalytics import log_this

@log_this()
def add(a, b):
    return a + b

add(10, 20)
Calling: __main__.add [2025-07-22T11:35:47.437833+00:00  2025-07-22T11:35:47.438144+00:00] Values: {'a': 10, 'b': 20} Attrs: {} Extra: {}
30
```

Every time the `add` function gets called, the given arguments are logged so you can later analyze the user behavior.

### You also get:

- Start/end time, which helps audit how fast/slow that particular function is, and if certain inputs cause it to slow down.
- Module name: Where the function is being called from.
- Values: Get the actuall arguments supplied to your functions (whether default or explicit).
- Attrs: In some cases you don't want to log the actual arguments. They might be uploaded images, CSV files, sensitive/private data, extremely long strings, or anything that would unnecessarily clutter your log files. In such cases, you can only log certain attribtes of those inputs. For example image size, CSV file dimensions, or string lengths, respectively.

## Installation

```bash
python3 -m pip install functionalytics
```

## Function parameters

- `log_level`: The level of logging required to trigger a logging event.
- `file_path`: The path of the file where you want to write and store the logs.  
- `log_format`: In case you want to have a different format.  
- `param_attrs`: A dictionary with keys being parameter names, and values being a transformer function for each. For example, if you have a string user input that you only want to log its length, you can supply something like this: `{"user_input": len}`.
- `discard_params`: Typically, when you have certain inputs that might clutter log files (or might be private), and that you want to log certain attributes, you will also need to discard those inputs from being logged. This is the option for doing so.
- `extra_data`: Allows for logging arbitrary additional data. This should be a dictionary where keys are strings (descriptions of the data) and values are the actual data to be logged. This gives developers the flexibility to include any custom information relevant to their needs.
- `error_file_path`: Just like `file_path` this optional file is where errors get logged, together with the full traceback.
- `log_conditions`: You don't always want to log a function call. Sometimes a function would be called with default values which the user didn't initiate, or maybe the default is an empty value, and you don't want to pollute the logs with those. For this parameter you supply a dictionary with the condition(s):

```python
log_conditions = {
    "param_a": lambda a: a is not None,
    "param_b": lambda b: b > 10,
    "param_c": lambda c: c in ["blue", "green", "organe"],
}

log_this(log_conditions=log_conditions)
```

The logging in this case would only occur if `param_a` is not `None` AND `param_b` is greater than 10, AND `param_c` is one of  `["blue", "green", "organe"]`. Maybe you're only interested in analyzing `param_b` inputs that are big enough so you can audit/analyze those, because you know that it's performing well on values less than 10. You also only want to check what happens only for the colors of interest which you can supply as shown above.
