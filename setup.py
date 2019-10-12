from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name="em-pyquil",
    version='1.0.2',
    author="Gate42 Quantum Computing Lab",
    author_email="team@gate42.org",
    description="A Python library implementing error mitigation on pyquil programs.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/gate42qc/em-pyquil.git",
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