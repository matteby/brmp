from functools import partial

from jax import random, vmap
from jax.config import config; config.update("jax_platform_name", "cpu")

from numpyro.handlers import substitute
from numpyro.hmc_util import initialize_model
from numpyro.mcmc import mcmc

from pyro.contrib.brm.backend import Backend, Model, apply_default_hmc_args
from pyro.contrib.brm.fit import Posterior
from pyro.contrib.brm.numpyro_codegen import gen

# The types described in the comments in pyro_backend.py as follows
# in this back end:
#
# bs: dict from parameter names to JAX numpy arrays
# ps: JAX numpy array

def get_param(samples, name):
    assert type(samples) == dict
    # Reminder to use correct interface.
    assert not name == 'mu', 'Use `location` to fetch `mu`.'
    return samples[name]

# Extract the underlying numpy array (rather than using JAX numpy) to
# match the interface exactly.
def to_numpy(param_samples):
    return param_samples._value if hasattr(param_samples, '_value') else param_samples

# I would ideally like to transform the numpy array into a JAX array
# here, in order to comply with the interface as closely as possible.
# However, since I don't know a super cheap way to do this, and given
# that these two types are mostly interchangable, I'll just use the
# identity here.
def from_numpy(data):
    return data

# TODO: Better name.
def run_model_on_samples_and_data(modelfn, samples, data):
    return vmap(lambda sample: substitute(modelfn, sample)(**data))(samples)

def nuts(data, model, seed=0, iter=None, warmup=None):
    assert type(data) == dict
    assert type(model) == Model

    iter, warmup = apply_default_hmc_args(iter, warmup)

    rng = random.PRNGKey(seed)
    init_params, potential_fn, constrain_fn = initialize_model(rng, model.fn, **data)
    samples = mcmc(warmup, iter, init_params,
                   potential_fn=potential_fn,
                   constrain_fn=constrain_fn,
                   print_summary=False)

    # Here we re-run the model on the samples in order to collect
    # transformed parameters. (e.g. `b`, `mu`, etc.) Theses are made
    # available via the return value of the model.
    transformed_samples = run_model_on_samples_and_data(model.fn, samples, data)
    all_samples = dict(samples, **transformed_samples)

    # TODO: Grab `mu` from `transformed_samples` when data is that
    # used for inference.
    def loc(data):
        return run_model_on_samples_and_data(model.fn, samples, data)['mu']

    return Posterior(all_samples, partial(get_param, all_samples), loc)

def svi(*args, **kwargs):
    raise NotImplementedError

# TODO: Make it possible to run inference on a gpu.

backend = Backend('NumPyro', gen, nuts, svi, from_numpy, to_numpy)
