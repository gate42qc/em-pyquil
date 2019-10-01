import numpy as np
from pyquil.api import get_qc
from pyquil.quil import Program
from pyquil.gates import X
from em_pyquil import apply_em, apply_noise

noisy_qc = apply_noise(get_qc("3q-qvm"))
em_qc = apply_em(get_qc("3q-qvm"))

p = Program(X(0))

em_res = em_qc.run_and_measure(p, 1000)  # results obtained running the program with noise and filtered with EM technique

noisy_res = noisy_qc.run_and_measure(p, 1000)  # results obtained running the program with just noise model without filtering

print("Noise + EM results", np.mean(em_res[0]))
print("Only Noise results", np.mean(noisy_res[0]))
