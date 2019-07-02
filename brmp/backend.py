from collections import namedtuple

# For now, assume that each back end provides a single inference algorithm.
Backend = namedtuple('Backend', 'name gen infer')

# We could have a class that wraps a (function, code) pair, making the
# code available via a code property and the function available via
# __call__. `GenModel` could also be callable. Too cute?
GenModel = namedtuple('GenModel', [
    'fn', 'code',
    'inv_link_fn', 'inv_link_code',
    'expected_response_fn', 'expected_response_code',
])