import numpy as np
from copy import deepcopy


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def copy(self):
        new_dotdict = dotdict()
        for key, value in self.items():
            if type(value) is dotdict:
                new_value = value.copy()
            else:
                new_value = deepcopy(value)
            new_dotdict[key] = new_value
        return new_dotdict

    def __deepcopy__(self, memo=None):
        return dotdict(deepcopy(dict(self), memo=memo))


def max_dif(signal1, signal2, t=(0, 150)):
    #return np.max(np.abs(signal1[t[0]:t[1]] - signal2[t[0]:t[1]]))
    return np.percentile(np.abs(signal1[t[0]:t[1]] - signal2[t[0]:t[1]]), 95.0) #Más estable con percentil 95 que con el máximo.

def transient_selectivity(signal1, signal2, t_stable=(2000, 2500), t_transit=(1500, 1700)):
    _S1 = np.mean(signal1[t_stable[0]:t_stable[1]])
    _S2 = np.mean(signal2[t_stable[0]:t_stable[1]])
    dif = max_dif(signal1, signal2, t_transit)
    return 1.0 - ((_S1 - _S2) / dif)

def steadystate_selectivity(signal, t_pre=(0, 50), t_stable=(300, 400)):
    SP_X = np.mean(signal[t_pre[0]:t_pre[1]])
    S_X = np.mean(signal[t_stable[0]:t_stable[1]])
    return 100*(1.0 - (S_X / SP_X))
