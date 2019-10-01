from setuptools import setup


setup(
    name="em-pyquil",
    version='1.0.0',
    author="Gate42 Quantum Computing Lab",
    author_email="team@gate42.org",
    description="A Python library implementing error mitigation on pyquil programs.",
    url="https://github.com/maghamalyan/em-pyquil.git",
    packages=["em_pyquil"],
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'numpy',
        'pyquil>=2.10.0',
    ],
    keywords='quantum quil programming pyquil error mitigation',
    python_requires=">=3.6",
)