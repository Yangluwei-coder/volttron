from setuptools import setup, find_packages

setup(
    name='fan_agent',
    version='1.0',
    packages=find_packages(),
    entry_points={
        'volttron.agent': [
            'launch = fan_agent.agent:main'
        ]
    },
    install_requires=['volttron']
)
