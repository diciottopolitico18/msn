import nest

from msn import MSN


class Experiment:

    def __init__(self):
        raise NotImplementedError("'Experiment' is a virtual class, you need to inherit it.")

    def run(self):
        raise NotImplementedError("'Experiment' is a virtual class, you need to inherit it.")

    def plot(self):
        raise NotImplementedError("'Experiment' is a virtual class, you need to inherit it.")


class ExperimentDAHD(Experiment):
    # The protocol (rates and durations) is in msn_params.py, params.exp.

    def __init__(s, dopamine_level=0.3, msn=None):

        # Initial values
        s.msn = MSN() if msn is None else msn

        # Setting dopamine
        s.dopamine_level = dopamine_level
        s.msn.params.neuron.msn_d1.phi_1 = dopamine_level
        s.msn.params.neuron.msn_d1.phi_2 = dopamine_level
        s.msn.params.neuron.msn_d2.phi_1 = dopamine_level
        s.msn.params.neuron.msn_d2.phi_2 = dopamine_level

        # Configurando el modelo
        s.msn.configure()


    def ramp_rates(s):
        """Total Poisson rate (afferent rate x afferents) of channels 0 and 1 in each step of the ramp."""
        exp = s.msn.params.exp
        m = exp.ctx_low_Hz * s.msn.params.net.ctx_afferents_per_neuron
        M = exp.ctx_high_Hz * s.msn.params.net.ctx_afferents_per_neuron
        n = exp.ramp_steps
        # Primera mitad de la rampa: both channels rise together towards the middle rate
        first = [(m + (M-m)*(i/(2*n)), m + (M-m)*(i/(2*n))) for i in range(n)]
        # Segunda mitad: the selected channel keeps rising, the other one goes back down
        second = [((m+M)*0.5 + (M-m)*(i/(2*n)), (m+M)*0.5 - (M-m)*(i/(2*n))) for i in range(n)]
        return first + second


    def run(s, warming_up_time=None):
        exp = s.msn.params.exp
        warming_up_time = exp.t_warmup if warming_up_time is None else warming_up_time
        m = exp.ctx_low_Hz * s.msn.params.net.ctx_afferents_per_neuron

        # Estado inicial: every channel (also the background one) at the low rate
        for channel in s.msn.poisson:
            nest.SetStatus(channel, {'rate': m})
        nest.Simulate(warming_up_time)

        # Ramp, one step at a time
        for rate_0, rate_1 in s.ramp_rates():
            nest.SetStatus(s.msn.poisson[0], {'rate': rate_0})
            nest.SetStatus(s.msn.poisson[1], {'rate': rate_1})
            nest.Simulate(exp.ramp_step_ms)

        # Finalización
        nest.Simulate(exp.t_steady)
