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

    # Frecuencias de disparo de la neurona cortical
    cortex_low_freq  = 2.2
    cortex_high_freq = 3.6



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


    def run(s, warming_up_time=1500):
        m = s.cortex_low_freq * s.msn.params.net.ctx_afferents_per_neuron
        M = s.cortex_high_freq * s.msn.params.net.ctx_afferents_per_neuron

        # Estado inicial, se mantiene por dos segundos
        for channel in s.msn.poisson:
            nest.SetStatus(channel, {'rate': m})
        nest.SetStatus(s.msn.poisson[0], {'rate': m})
        nest.SetStatus(s.msn.poisson[1], {'rate': m})
        nest.Simulate(warming_up_time)

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
