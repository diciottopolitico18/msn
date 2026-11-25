"""
Original analysis code of msn.py and experiment.py (Rusiecka 2022, from Gonzalez-Redondo et al. 2020).
Moved here unchanged on 2026-11-25 (scheda F3.7; decision of 2026-11-03 in the project notes).

THIS FILE IS NOT IMPORTED BY ANYTHING AND DOES NOT RUN WITH NEST 3.8:
  - MSN.get_activity, MSN.signal, MSN._compute_signals: GetConnections(target=[...]) fails in NEST 3;
    _compute_signals also uses scipy.signal and itemgetter, never imported in msn.py;
  - MSN.plot_raster, ExperimentDAHD._plot_network: use utils/raster_plot.py, a copy of the NEST 2
    raster_plot module, removed from the project at the same time (recover it with
    git show 271ef8b:"MSN code/utils/raster_plot.py");
  - Experiment.transient_selectivity / steadystate_selectivity and ExperimentSSTS: refer to s.bg,
    _params, restart_kernel and tqdm, left over from the full basal ganglia model.
The working versions of the smoothed signal and of the selectivity metrics are in analysis/metrics.py.

WHERE EACH PIECE CAME FROM (line numbers in commit 271ef8b, the last one before the move):
  MSN code/msn.py, class MSN
      get_activity                                  lines 235-287
      plot_raster                                   lines 290-317
      _compute_signals                              lines 320-327
      signal                                        lines 330-348
  MSN code/experiment.py
      class Experiment:    transient_selectivity    lines 28-29
                           steadystate_selectivity  lines 32-33
      class ExperimentDAHD: plot                    lines 91-94
                           _plot_network            lines 96-100
      class ExperimentSSTS (whole class)            lines 104-219
  MSN code/01 - General behaviour.ipynb -> moved as is to legacy/01 - General behaviour.ipynb
To see a file as it was:  git show 271ef8b:"MSN code/msn.py"
To put a method back: copy it from here into the same class of that file and restore its imports
(raster_plot, scipy.signal, itemgetter, ...); note that it still has to be fixed for NEST 3.8.
"""


# ---------------------------------------------------------------- from MSN code/msn.py, class MSN (lines 235-348)
class MSN:

    def get_activity(s, nucleus_name, channels=True, frequency=True, time_range=None, time_bin=50, n_bins=None):
        nucleus_name = nucleus_name.lower()
        s.__getattribute__(nucleus_name)

        if type(channels) is bool and channels == False:
            detector = s.__getattribute__('spikedetector_' + nucleus_name)
        elif (type(channels) is bool and channels == True):
            detector = [d[0] for d in s.__getattribute__('spikedetector_' + nucleus_name + '_channels')]
        elif type(channels) is int:
            detector = [d[0] for idx, d in
                        enumerate(s.__getattribute__('spikedetector_' + nucleus_name + '_channels'))
                        if channels == idx]
        elif type(channels) is list:
            detector = [d[0] for idx, d in
                        enumerate(s.__getattribute__('spikedetector_' + nucleus_name + '_channels'))
                        if idx in channels]
        else:
            raise ValueError('Parameter `channel` must be bool, int or list of ints.')

        nucleus_spike_times = [d['times'] for d in nest.GetStatus(detector, 'events')]
        n_senders_channel = [len(nest.GetConnections(target=[d])) for d in detector]

        time_range = (0, nest.GetKernelStatus('time')) if time_range == None else time_range

        if n_bins:
            time_bin = (time_range[1] - time_range[0]) / n_bins
        else:
            n_bins = int((time_range[1] - time_range[0]) / time_bin)

        count_channel = []

        if frequency:
            for ch, n_senders in zip(nucleus_spike_times, n_senders_channel):
                count, interval = np.histogram(
                    ch,
                    bins=n_bins,
                    range=time_range,
                    weights=np.ones_like(ch) / (n_senders * (time_bin / 1000.0))
                )
                count_channel.append(count)
                intervals = interval

        else:
            for ch in nucleus_spike_times:
                count, interval = np.histogram(
                    ch,
                    bins=n_bins,
                    range=time_range,
                )
                count_channel.append(count)
                intervals = interval

        return intervals, count_channel


    def plot_raster(s, nucleus_name, channels=False, time_range=None, time_bin=50, n_bins=None, y_range=None):
        nucleus_name = nucleus_name.lower()
        s.__getattribute__(nucleus_name)

        if type(channels) is bool and channels == False:
            detectors = [s.__getattribute__('spikedetector_' + nucleus_name)]
        elif (type(channels) is bool and channels == True):
            detectors = [d[0] for d in s.__getattribute__('spikedetector_' + nucleus_name + '_channels')]
        elif type(channels) is int:
            detectors = [d[0] for idx, d in
                        enumerate(s.__getattribute__('spikedetector_' + nucleus_name + '_channels'))
                        if channels == idx]
        elif type(channels) is list:
            detectors = [d[0] for idx, d in
                        enumerate(s.__getattribute__('spikedetector_' + nucleus_name + '_channels'))
                        if idx in channels]
        else:
            raise ValueError('Parameter `channel` must be bool, int or list of ints.')

        time_range = (0, nest.GetKernelStatus('time')) if time_range == None else time_range

        if n_bins:
            time_bin = (time_range[1] - time_range[0]) / n_bins
        else:
            n_bins = int((time_range[1] - time_range[0]) / time_bin)

        for d in detectors:
            raster_plot.from_device(d, hist_binwidth=time_bin, ylim=y_range)


    def _compute_signals(s, nucleus='msn', time_range=None, mode='gaussian_convolution'):
        time_range = (0, 2500) if time_range is None else time_range

        if mode == 'gaussian_convolution':
            times, spikes_channels = s.get_activity(nucleus, time_bin=1)
            win = signal.gaussian(M=50, std=7.5)
            sum_win = sum(win)
            s._signals[nucleus] = [signal.convolve(s, win, mode='same')[time_range[0]:time_range[1]]/sum_win for s in spikes_channels]


    def signal(s, nucleus, channels=True, *args, **kwargs):

        try:
            s.__getattribute__('_signals')
        except AttributeError:
            s._signals = {}

        if not nucleus in s._signals:
            s._compute_signals(nucleus, *args, **kwargs)

        if type(channels) is bool:
            if channels==True:
                channels = list(range(len(s.params.net.p_channels)))
            else:
                return None #Why do this? Maybe to make sure that values are precomputed?
        elif type(channels) is int:
            channels = [channels]

        return itemgetter(*channels)(s._signals[nucleus])


# ---------------------------------------------------------------- from MSN code/experiment.py, class Experiment (lines 28-33)
class Experiment:

    def transient_selectivity(s, nucleus='msn'):
        return transient_selectivity(s.bg.signal(nucleus,0), s.bg.signal(nucleus,1), t_stable=(2000, 2500), t_transit=(1500, 1700))


    def steadystate_selectivity(s, nucleus='msn'):
        return steadystate_selectivity(s.bg.signal(nucleus,1), t_pre=(1250, 1500), t_stable=(2000, 2500))


# ---------------------------------------------------------------- from MSN code/experiment.py, class ExperimentDAHD (lines 91-100)
class ExperimentDAHD(Experiment):

    # @verbose(_params.sim.verbose)
    def plot(s):
        s._plot_network()
        plt.show()

    # @verbose(_params.sim.verbose)
    def _plot_network(s):
        plt.rcParams['figure.figsize'] = [3.0, 8.0]
        for i in range(len(_params.net.p_channels)):
            raster_plot.from_device(s.msn.spikedetector_msn_channels[i], hist_binwidth=s.time_bin, title='Canal {}'.format(i + 1), ylim=(0, 40))


# ---------------------------------------------------------------- from MSN code/experiment.py, whole class ExperimentSSTS (lines 104-219)
class ExperimentSSTS(Experiment):

    # Frecuencias de disparo de la neurona cortical
    cortex_low_freq  = 2.2
    cortex_high_freq = 3.6
    time_range = (0, 3550)


    def __init__(s):
        resolution=8

        s.da_values = np.linspace(start=0.0, stop=1.0, num=resolution)
        s.hd_values = np.linspace(start=0.0, stop=1.0, num=resolution)
        s.pd_values = np.linspace(start=0.0, stop=1.0, num=resolution)

        s.signal_hd_msn = np.zeros((s.hd_values.size, s.da_values.size, len(_params.net.p_channels), s.time_range[1]-s.time_range[0]))
        # s.signal_hd_snr = np.zeros((s.hd_values.size, s.da_values.size, len(_params.net.p_channels), s.time_range[1]-s.time_range[0]))
        s.signal_pd_msn = np.zeros((s.hd_values.size, s.da_values.size, len(_params.net.p_channels), s.time_range[1]-s.time_range[0]))
        # s.signal_pd_snr = np.zeros((s.hd_values.size, s.da_values.size, len(_params.net.p_channels), s.time_range[1]-s.time_range[0]))

        s.results_ts_hd_msn = np.zeros((s.hd_values.size, s.da_values.size))
        s.results_ss_hd_msn = np.zeros((s.hd_values.size, s.da_values.size))
        s.results_ts_pd_msn = np.zeros((s.pd_values.size, s.da_values.size))
        s.results_ss_pd_msn = np.zeros((s.pd_values.size, s.da_values.size))

        s.msn = None
        s.iterations = None


    def _configure_new_run(s, dopamine_level=0.3, huntington_level=0.0):
        restart_kernel()

        # Initial values
        s.msn = MSN()

        # Setting the model
        # s.bg.params.net.snr.n = 3000 #More neurons in SNr to have more stable measurements

        # Setting dopamine
        s.msn.params.neuron.msn_d1.phi_1 = dopamine_level
        s.msn.params.neuron.msn_d1.phi_2 = dopamine_level
        s.msn.params.neuron.msn_d2.phi_1 = dopamine_level
        s.msn.params.neuron.msn_d2.phi_2 = dopamine_level

        # # Setting Huntington
        # s.bg.params.syn.ctx_msn.syn_spec_nmda.weight = (3.05 + 3.05*huntington_level) / s.bg.params.neuron.msn_d1.tau_syn[1]
        # s.bg.params.net.msn.d2_n = int(s.bg.params.net.msn.n * 0.5 * (1.0 - huntington_level*0.8))

        # Configurando el modelo
        s.bg.configure()


    def _run_one(s):
        m = s.cortex_low_freq * s.bg.params.net.ctx_afferents_per_neuron
        M = s.cortex_high_freq * s.bg.params.net.ctx_afferents_per_neuron

        # Estado inicial, se mantiene por dos segundos
        for channel in s.msn.poisson:
            nest.SetStatus(channel, {'rate': m})
        nest.SetStatus(s.msn.poisson[0], {'rate': m})
        nest.SetStatus(s.msn.poisson[1], {'rate': m})
        nest.Simulate(2500.0)

        # Primera mitad de la rampa, durante 25 ms
        for i in range(25):
            fi = i/50.0
            nest.SetStatus(s.msn.poisson[0], {'rate': m + (M-m)*fi})
            nest.SetStatus(s.msn.poisson[1], {'rate': m + (M-m)*fi})
            nest.Simulate(1.0)

        # Segunda mitad de la rampa, durante 25 ms
        for i in range(25):
            fi = i/50.0
            nest.SetStatus(s.msn.poisson[0], {'rate': (m+M)*0.5 + (M-m)*fi})
            nest.SetStatus(s.msn.poisson[1], {'rate': (m+M)*0.5 - (M-m)*fi})
            nest.Simulate(1.0)

        # Finalización, 1000 ms
        nest.Simulate(1000.0)


    def transient_selectivity(s, nucleus='msn'):
        return transient_selectivity(s.msn.signal(nucleus,0), s.msn.signal(nucleus,1), t_stable=(3000, 3500), t_transit=(2500, 2700))


    def steadystate_selectivity(s, nucleus='msn'):
        return steadystate_selectivity(s.msn.signal(nucleus,1), t_pre=(2000, 2400), t_stable=(3000, 3500))


    def run(s, times=1, plot=False):
        i_times = 1.0/times
        s.iterations = times if s.iterations==None else s.iterations+times
        conditions_hd = itertools.product(enumerate(s.hd_values), enumerate(s.da_values), range(times))
        conditions_pd = itertools.product(enumerate(s.hd_values), enumerate(s.da_values), range(times))

        for (i, hd), (j, da), _ in tqdm(conditions_hd, total=s.hd_values.size*s.da_values.size*times):
            s._configure_new_run(dopamine_level=da, huntington_level=hd)
            s._run_one()

            for idx_ch, _ in enumerate(s.bg.params.net.p_channels):
                s.signal_hd_msn[j,i,idx_ch,:] += s.msn.signal('msn',idx_ch,time_range=s.time_range)[:] * i_times
                s.signal_hd_snr[j,i,idx_ch,:] += s.msn.signal('snr',idx_ch,time_range=s.time_range)[:] * i_times

            s.results_ts_hd_msn[j,i] += s.transient_selectivity(nucleus='msn') * i_times
            s.results_ts_hd_snr[j,i] += s.transient_selectivity(nucleus='snr') * i_times
            s.results_ss_hd_msn[j,i] += s.steadystate_selectivity(nucleus='msn') * i_times
            s.results_ss_hd_snr[j,i] += s.steadystate_selectivity(nucleus='snr') * i_times

            if plot:
                plt.rcParams['figure.figsize'] = [8.0, 3.0]
                plt.figure()
                s.bg.plot_activity('msn', channels=True, time_bin=20, frequency=True)
                _ = plt.title('DA: {}\nHD: {}'.format(da, hd))

    def plot(s):
        pass
