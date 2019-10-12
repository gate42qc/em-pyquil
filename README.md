# Error Mitigation Implemented on Rigetti Forest&trade;

The unwanted interaction of the quantum computer with the outside
world introduces noise into the computations which makes 
fault tolerant Quantum Computation outof reach of current technologies.
In this regard, to make use of NISQ devices one can consider techniques which
alleviate the impacts of errors without additional resource
requirements. One of such mitigation techniques (for
short depth circuits) is the so called ”Extrapolation to
the zero noise limit” or as we will refer to it Error Mitigation (EM)
which has been successfully [implemented recently](https://www.nature.com/articles/s41586-019-1040-7).
It is assumed that the action of the noise is weak and it can be described by
some small parameter. The expectation value of any
observable depends on this parameter and can be expanded
as series in it and the 0th order term will correspond
to noise-free value. It’s suggested to gain the 
expectation values at different noise parameters and then apply
Richardson’s deferred approach to the limit to obtain an
approximation to noise-free value. 

This package provides easy to use interface for applying error correcting code with EM technique to any PyQuil program.

EM in this package is implemented as described [here](https://arxiv.org/abs/1612.02058).

## Installation

EMPyQuil can be installed using pip, or directly from source.

To instead install EMPyQuil as a PyPI package, do the following:

`pip install em_pyquil`

If you would prefer to install EMPyQuil directly from source, do the following:

`pip install git+https://github.com/gate42qc/em-pyquil`


## Usage

This package provides two functions: `apply_em` and `apply_noise` which can be used with PyQuil `QuantumComputer` objects.
These functions will override `run` methods of passed `QuantumComputer` objects making them return error mitigated results.

So if you have some piece of code and want to run the error mitigated version of it you only need to call `apply_em` on `QuantumComputer` 
object you will use for running your program.

```python
from pyquil.api import get_qc
from pyquil.quil import Program
from pyquil.gates import X
from em_pyquil import apply_em, apply_noise

noisy_qc = apply_noise(get_qc("3q-qvm"))
em_qc = apply_em(get_qc("3q-qvm"))

p = Program(X(0))

em_res = em_qc.run_and_measure(p, 1000)  # results obtained running the program with noise and filtered with EM technique

noisy_res = noisy_qc.run_and_measure(p, 1000)  # results obtained running the program with just noise model without filtering
```

## Examples

There are more examples in the [examples directory](examples).


## Running your programs with EM technique applied

In our EM implementation we run the program 
multiple times with noise models with 
different values of the noise parameter 
(in current implementation noise parameter is the gate time).
Then we will collect result bitstrings, get mean results for each qubit over trials,
then using Richardson’s method we extrapolate results.
The extrapolated results are rounded to 0 or 1 and returned.

So after the following line:

`em_qc = apply_em(get_qc("3q-qvm"))`

the `em_qc` will work exactly like `QuantumComputer` instance would work 
except that it will run programs multiple times and will return extrapolated results.
This allows you to run you existing programs with EM 
without changing much of our existing code.

:note
Do not call `apply_noise` or `noisy_qc` on the same `QuantumComputer` object.


You can customise noise parameters used in EM by giving the base parameter and list of coefficients:

```python
# programs will run with gate times: 1*60e-9, 1.5*60e-9 and 2*60e-9
em_qc = apply_em(get_qc("3q-qvm"), base_gate_time=60e-9, noise_param_coefficients=[1, 1.5, 2])
```

## Comparing noisy and noise + EM results

There is another function: `apply_noise` in this package you could use to 
obtain `QuantumComputer` instance that uses similar noise 
model to `apply_em` so that you can compare results:

```python
import numpy as np
import matplotlib.pyplot as plt
import random

from pyquil.api import get_qc
from pyquil.quil import Program
from pyquil.gates import RX, RZ, CZ

from em_pyquil import apply_em, apply_noise


def get_dagger_of_native_gate(gate):
    if gate.name == "RZ":
        return RZ(-gate.params[0], gate.qubits[0])
    if gate.name == "RX":
        return RX(-gate.params[0], gate.qubits[0])
    if gate.name == "CZ":
        return CZ(*gate.qubits)

    raise ValueError("Unsupported gate: " + str(gate))


def get_random_circuit(qubits, length, two_qubit_gate_portion=0.3):
    p = Program()

    for i in range(int(length / 2)):
        if (len(qubits) > 1) and (random.random() < two_qubit_gate_portion):
            random_gate = CZ(*(random.sample(qubits, 2)))
        else:
            theta = 2 * np.pi * random.random()
            qubit = random.choice(qubits)
            random_gate = random.choice([
                RZ(theta, qubit),
                RX(np.pi / 2, qubit),
                RX(- np.pi / 2, qubit)
            ])

        p.inst(random_gate)

    for gate in reversed(Program(p.out()).instructions):
        p.inst(get_dagger_of_native_gate(gate))

    return Program('PRAGMA PRESERVE_BLOCK') + p + Program('PRAGMA END_PRESERVE_BLOCK')


def run_with_qc(qc, lengths):
    data = []

    for i in lengths:
        fidelities = []
        for j in range(20):
            p = get_random_circuit(qc.qubits(), i)
            res = qc.run_and_measure(p, 10000)
            fidelity = 1 - np.mean(res[0] * res[1])
            fidelities.append(fidelity)
        mean_fidelity = np.mean(np.array(fidelities))
        data.append(mean_fidelity)

    return data


noisy_qc = apply_noise(get_qc("3q-qvm"))
em_qc = apply_em(get_qc("3q-qvm"))

lengths = np.arange(2, 100, 5)

em_data = run_with_qc(em_qc, lengths)
noisy_data = run_with_qc(noisy_qc, lengths)

plt.xlabel('Circuit depth')
plt.ylabel('Fidelity')
plt.plot(lengths, noisy_data, 'o-', label="Only Noise")
plt.plot(lengths, em_data, 'o-', label="Noise + EM")
plt.legend()
plt.show()

```