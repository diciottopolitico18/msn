import nest

from msn_params import params


def setup_kernel(dt=None, seed=None, threads=None, verbosity="M_ERROR"):
    """Reset the NEST kernel and prepare it for an MSN simulation.

    Arguments left as None fall back to params.sim (step, seed, n_threads).
    Must be called before creating any node.
    """
    dt = params.sim.step if dt is None else dt
    seed = params.sim.seed if seed is None else seed
    threads = params.sim.n_threads if threads is None else threads

    nest.ResetKernel()
    nest.set_verbosity(verbosity)
    # ResetKernel unloads external modules in NEST 3.x, so msn_neuron must be reinstalled after every reset
    nest.Install("nestmlmodule")
    nest.SetKernelStatus({"resolution": dt, "rng_seed": seed, "local_num_threads": threads})
