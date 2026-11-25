"""
Code of the original model that the striatum-only network never uses (Rusiecka 2022, from
Gonzalez-Redondo et al. 2020). Moved here unchanged on 2026-11-25 (cleanup "group B").

THIS FILE IS NOT IMPORTED BY ANYTHING. It works with NEST 3.8 but is dead code here:
  - MSN._create_msn, first branch: if params.net.msn.is_active is a NUMBER instead of True, the MSNs
    are replaced by parrot neurons driven by one Poisson generator at that rate ("un sustituto de
    este nucleo"), reduced by params.net.msn.reduction_factor. In the full basal ganglia model of
    Gonzalez-Redondo (github.com/EduardoRosLab/BG_selectivity, commit 3596d11) every nucleus has
    this switch, to replace it with a fixed-rate source while studying the others. In the
    striatum-only model is_active is always True, so the branch never runs.
    The same switch also guarded the cortex->MSN and MSN->MSN connections and the multimeter
    (`if type(s.params.net.msn.is_active) is bool:` in _create_connections and _create_detectors);
    those guards were removed from msn.py.
  - utils.split_in_groups: splits neurons into channels; only the parrot branch used it (the MSN
    branch uses msn._split_by_proportions).
  - utils.custom_exceptions.ParamError: only raised by split_in_groups.
  - params.net.msn.reduction_factor: only read by the parrot branch.
  - utils.verbose: decorator printing the running time of a method; used only in commented-out
    lines (`# @verbose(_params.sim.verbose)` in experiment.py), configured by is_verbose.
  - utils.log_progress: progress bar for Jupyter notebooks (needs ipywidgets), never called.
  - utils.smooth: moving-window smoothing, never called (analysis/metrics.py smooths with a Gaussian).

WHERE EACH PIECE CAME FROM (line numbers in commit b31fa6f, the last one before the move):
  MSN code/msn.py, class MSN, _create_msn (both branches, as they were)   lines 48-100
  MSN code/utils/__init__.py, split_in_groups                             lines 8-25
  MSN code/utils/custom_exceptions.py, ParamError (whole file)            lines 1-7
  MSN code/msn_params.py, reduction_factor                                line 47
  MSN code/utils/__init__.py, verbose (decorator) + its import           lines 48-63
  MSN code/utils/__init__.py, log_progress (Jupyter progress bar)        lines 82-164
  MSN code/utils/__init__.py, smooth + its `import numpy`                lines 167-184
    (and the imports used only by log_progress: lines 3-4 `system_time`, `floor`)
  MSN code/msn_params.py, is_verbose / params.sim.verbose (only for verbose)  lines 9, 28
To see a file as it was:  git show b31fa6f:"MSN code/msn.py"
To put the parrot substitute back: restore the first branch of _create_msn, split_in_groups,
ParamError and reduction_factor, and the `is bool` guards in _create_connections/_create_detectors.
"""


# ---------------------------------------------------------------- from MSN code/msn.py, class MSN (lines 48-100)
class MSN:

    def _create_msn(s):
        # Queremos crear un sustituto de este núcleo que dispare a una frecuencia determinada
        if type(s.params.net.msn.is_active) is not bool:
            #creating a parrot neuron, half the amount of msn neurons, times the reduction factor for using the poisson population
            s.msn_d1 = nest.Create('parrot_neuron', int(s.params.net.msn.d1_n * s.params.net.msn.reduction_factor))

            #creating a parrot neuron, half the amount of msn neurons, times the reduction factor for using the poisson population
            s.msn_d2 = nest.Create('parrot_neuron', int(s.params.net.msn.d2_n * s.params.net.msn.reduction_factor))

            #adding the neuron populations
            s.msn = s.msn_d1 + s.msn_d2

            #poisson generator will generate a unique spike train for all of its targets, you have to use a parrot neuron in between the poisson generator and the target
            s.msn_poisson = nest.Create('poisson_generator', 1, {'rate': s.params.net.msn.is_active})
            nest.Connect(s.msn_poisson, s.msn)

            #returning a list of lists with neurons for each channel
            s.msn_d1_channels = split_in_groups(s.msn_d1, s.params.net.p_channels)
            s.msn_d2_channels = split_in_groups(s.msn_d2, s.params.net.p_channels)

            #aggregating the number of d1 and d2 neurons for each channel
            s.msn_channels = [d1+d2 for (d1,d2) in zip(s.msn_d1_channels, s.msn_d2_channels)]
            #creating the striatal channels to look like msn
            s.str_channels = deepcopy(s.msn_channels)

        # Queremos crear el núcleo normal
        else:
            #creating msn neurons
            s.msn_d1 = nest.Create('msn_neuron', s.params.net.msn.d1_n)
            s.msn_d2 = nest.Create('msn_neuron', s.params.net.msn.d2_n)
            nest.SetStatus(s.msn_d1, s.params.neuron.msn_d1)
            nest.SetStatus(s.msn_d2, s.params.neuron.msn_d2)

            #for if curve
            # nest.SetStatus(s.msn_d1, {'I_e': s.curr})

            #combining the 2 populations of neurons
            s.msn = s.msn_d1 + s.msn_d2

            #returning a list of lists with neurons for each channel 
            s.msn_d1_channels = _split_by_proportions(s.msn_d1, s.params.net.p_channels)
            s.msn_d2_channels = _split_by_proportions(s.msn_d2, s.params.net.p_channels)
            #aggregating the number of d1 and d2 neurons for each channel 
            s.msn_channels = [d1+d2 for (d1,d2) in zip(s.msn_d1_channels, s.msn_d2_channels)]

            #assigning for the striatal channels to be equal to msn channels
            for i in range(len(s.str_channels)):
                s.str_channels[i] = s.msn_channels[i]

            # Establezco valores iniciales de las neuronas. Pongo el voltaje al mínimo
            #putting the initial voltage to minimum
            dUVms = [{"V_m": s.params.neuron.msn_d1.vp} for _ in s.msn]
            nest.SetStatus(s.msn, dUVms)


# ---------------------------------------------------------------- from MSN code/utils/__init__.py (lines 8-25)
def split_in_groups(an_iterable, proportions):
    proportions = proportions[:]
    groups = [[]]

    pos = 0.0
    step = sum(proportions) / len(an_iterable)
    for e in an_iterable:
        if proportions and pos > proportions[0]:
            proportions.pop(0)
            groups.append([])
            pos = 0
        pos += step
        groups[-1].append(e)

    for group in groups:
        if len(group) == 0: raise ParamError("Unknown variable", "A channel has zero neurons.")

    return groups


# ---------------------------------------------------------------- from MSN code/utils/custom_exceptions.py (lines 1-7)

class ParamError(Exception):
    """Any kind of error related to parameters values."""
    def __init__(self, param_name, msg=None):
        msg = "Some problem occured with parameter {}.".format(param_name) if msg is None else msg
        super().__init__(msg)
        self.param_name = param_name


# ---------------------------------------------------------------- from MSN code/msn_params.py (line 47)
params.net.msn.reduction_factor = 1.0 / 10.0 #Cuando se usa una población poisson en lugar del msn, reducimos el número de neuronas para acelerar los calculos.


# ---------------------------------------------------------------- from MSN code/utils/__init__.py (lines 3-4, 48-63, 82-164, 167-184)
from time import time as system_time
from math import floor

from time import time
def verbose(verbose=True):

    def decorator(f):
        if not verbose: return f

        def wrapped_func(*args, **kwargs):
            print("Entering {}...".format(f.__name__))
            running_time = time()
            f(*args, **kwargs)
            running_time = time() - running_time
            print("Exited {} after {} seconds.\n".format(f.__name__, running_time))

        return wrapped_func

    return decorator


def log_progress(sequence, every=None, size=None, name='Items'):
    # https://github.com/kuk/log-progress

    from ipywidgets import IntProgress, HTML, VBox
    from IPython.display import display

    is_iterator = False
    if size is None:
        try:
            size = len(sequence)
        except TypeError:
            is_iterator = True
    if size is not None:
        if every is None:
            if size <= 200:
                every = 1
            else:
                every = int(size / 200)     # every 0.5%
    else:
        assert every is not None, 'sequence is iterator, set every'

    if is_iterator:
        progress = IntProgress(min=0, max=1, value=1)
        progress.bar_style = 'info'
    else:
        progress = IntProgress(min=0, max=size, value=0)
    label = HTML()
    box = VBox(children=[label, progress])
    display(box)

    index = 0
    full_init_time = system_time()
    elapsed_time = system_time()
    try:
        for index, record in enumerate(sequence, 1):
            if index == 1 or index % every == 0:
                if is_iterator:
                    label.value = '{name}: {index} / ?'.format(
                        name=name,
                        index=index
                    )
                else:
                    time_per_case = (elapsed_time-full_init_time) / index

                    rem_time = time_per_case * (size-index+1)
                    hours = floor(rem_time / 3600.0)
                    minutes = floor((rem_time - hours*3600.0) / 60.0)
                    seconds = floor(rem_time - minutes*60.0 - hours*3600)
                    rem_time = "{hours}:{minutes:02}:{seconds:02}".format(hours=hours, minutes=minutes, seconds=seconds)

                    ela_time = elapsed_time - full_init_time
                    hours = floor(ela_time / 3600.0)
                    minutes = floor((ela_time - hours*3600.0) / 60.0)
                    seconds = floor(ela_time - minutes*60.0 - hours*3600)
                    ela_time = "{hours}:{minutes:02}:{seconds:02}".format(hours=hours, minutes=minutes, seconds=seconds)

                    progress.value = index
                    label.value = u'{name}: {index} / {size} - Ela: {ela_time}\nRem: {rem_time}'.format(
                        name=name,
                        index=index,
                        size=size,
                        ela_time=ela_time,
                        rem_time=rem_time
                    )
            yield record
            elapsed_time = system_time()
    except:
        progress.bar_style = 'danger'
        raise
    else:
        ela_time = system_time() - full_init_time
        hours = floor(ela_time / 3600.0)
        minutes = floor((ela_time - hours * 3600.0) / 60.0)
        seconds = floor(ela_time - minutes * 60.0 - hours * 3600)
        ela_time = "{hours}:{minutes:02}:{seconds:02}".format(hours=hours, minutes=minutes, seconds=seconds)

        progress.bar_style = 'success'
        progress.value = index
        label.value = "{name}: {index}. Total time: {ela_time}".format(
            name=name,
            index=str(index or '?'),
            ela_time=ela_time
        )


import numpy

def smooth(x,window_len=11,window='hanning'):
        if x.ndim != 1:
                raise(ValueError, "smooth only accepts 1 dimension arrays.")
        if x.size < window_len:
                raise(ValueError, "Input vector needs to be bigger than window size.")
        if window_len<3:
                return x
        if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
                raise(ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")
        s=numpy.r_[2*x[0]-x[window_len-1::-1],x,2*x[-1]-x[-1:-window_len:-1]]
        if window == 'flat': #moving average
                w=numpy.ones(window_len,'d')
        else:
                w=eval('numpy.'+window+'(window_len)')
        y=numpy.convolve(w/w.sum(),s,mode='same')
        return y[window_len:-window_len+1]


# ---------------------------------------------------------------- from MSN code/msn_params.py (lines 9 and 28)
is_verbose = [False, True][0]
params.sim.verbose = is_verbose
