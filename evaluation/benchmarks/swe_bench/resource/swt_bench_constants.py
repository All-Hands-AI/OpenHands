# Based on https://github.com/logic-star-ai/swt-bench/blob/master/src/constants.py

# Constants - Installation Specifications
MAP_VERSION_TO_INSTALL_SKLEARN = {
    k: {
        'python': '3.6',
        'packages': 'numpy scipy cython pytest pandas matplotlib',
        'install': 'python -m pip install -v --no-use-pep517 --no-build-isolation -e .',
        'pip_packages': [
            'cython',
            'numpy==1.19.2',
            'setuptools',
            'scipy==1.5.2',
        ],
    }
    for k in ['0.20', '0.21', '0.22']
}
MAP_VERSION_TO_INSTALL_SKLEARN.update(
    {
        k: {
            'python': '3.9',
            'packages': "'numpy==1.19.2' 'scipy==1.5.2' 'cython==3.0.10' pytest 'pandas<2.0.0' 'matplotlib<3.9.0' setuptools pytest joblib threadpoolctl",
            'install': 'python -m pip install -v --no-use-pep517 --no-build-isolation -e .',
            'pip_packages': ['cython', 'setuptools', 'numpy', 'scipy'],
        }
        for k in ['1.3', '1.4']
    }
)
MAP_VERSION_TO_INSTALL_FLASK = {
    '2.0': {
        'python': '3.9',
        'packages': 'requirements.txt',
        'install': 'python -m pip install -e .',
        'pip_packages': [
            'setuptools==70.0.0',
            'Werkzeug==2.3.7',
            'Jinja2==3.0.1',
            'itsdangerous==2.1.2',
            'click==8.0.1',
            'MarkupSafe==2.1.3',
        ],
    },
    '2.1': {
        'python': '3.10',
        'packages': 'requirements.txt',
        'install': 'python -m pip install -e .',
        'pip_packages': [
            'click==8.1.3',
            'itsdangerous==2.1.2',
            'Jinja2==3.1.2',
            'MarkupSafe==2.1.1',
            'Werkzeug==2.3.7',
        ],
    },
}
MAP_VERSION_TO_INSTALL_FLASK.update(
    {
        k: {
            'python': '3.11',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
            'pip_packages': [
                'click==8.1.3',
                'itsdangerous==2.1.2',
                'Jinja2==3.1.2',
                'MarkupSafe==2.1.1',
                'Werkzeug==2.3.7',
            ],
        }
        for k in ['2.2', '2.3']
    }
)
MAP_VERSION_TO_INSTALL_DJANGO = {
    k: {
        'python': '3.5',
        'packages': 'requirements.txt',
        'pre_install': [
            'apt-get update && apt-get install -y locales',
            "echo 'en_US UTF-8' > /etc/locale.gen",
            'locale-gen en_US.UTF-8',
        ],
        'install': 'python setup.py install',
        'pip_packages': ['setuptools'],
        'eval_commands': [
            'export LANG=en_US.UTF-8',
            'export LC_ALL=en_US.UTF-8',
            'export PYTHONIOENCODING=utf8',
            'export LANGUAGE=en_US:en',
        ],
    }
    for k in ['1.7', '1.8', '1.9', '1.10', '1.11', '2.0', '2.1', '2.2']
}
MAP_VERSION_TO_INSTALL_DJANGO.update(
    {
        k: {'python': '3.5', 'install': 'python setup.py install'}
        for k in ['1.4', '1.5', '1.6']
    }
)
MAP_VERSION_TO_INSTALL_DJANGO.update(
    {
        k: {
            'python': '3.6',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
            'eval_commands': [
                "sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen",
                'export LANG=en_US.UTF-8',
                'export LANGUAGE=en_US:en',
                'export LC_ALL=en_US.UTF-8',
            ],
        }
        for k in ['3.0', '3.1', '3.2']
    }
)
MAP_VERSION_TO_INSTALL_DJANGO.update(
    {
        k: {
            'python': '3.8',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
        }
        for k in ['4.0']
    }
)
MAP_VERSION_TO_INSTALL_DJANGO.update(
    {
        k: {
            'python': '3.9',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
        }
        for k in ['4.1', '4.2']
    }
)
MAP_VERSION_TO_INSTALL_DJANGO.update(
    {
        k: {
            'python': '3.11',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
        }
        for k in ['5.0']
    }
)
MAP_VERSION_TO_INSTALL_REQUESTS = {
    k: {'python': '3.9', 'packages': 'pytest', 'install': 'python -m pip install .'}
    for k in ['0.7', '0.8', '0.9', '0.11', '0.13', '0.14', '1.1', '1.2', '2.0', '2.2']
    + ['2.3', '2.4', '2.5', '2.7', '2.8', '2.9', '2.10', '2.11', '2.12', '2.17']
    + ['2.18', '2.19', '2.22', '2.26', '2.25', '2.27', '3.0']
}
MAP_VERSION_TO_INSTALL_SEABORN = {
    k: {
        'python': '3.9',
        'install': 'python -m pip install -e .',
        'pip_packages': [
            'contourpy==1.1.0',
            'cycler==0.11.0',
            'fonttools==4.42.1',
            'importlib-resources==6.0.1',
            'kiwisolver==1.4.5',
            'matplotlib==3.7.2',
            'numpy==1.25.2',
            'packaging==23.1',
            'pandas==1.3.5',  # 2.0.3
            'pillow==10.0.0',
            'pyparsing==3.0.9',
            'pytest',
            'python-dateutil==2.8.2',
            'pytz==2023.3.post1',
            'scipy==1.11.2',
            'six==1.16.0',
            'tzdata==2023.1',
            'zipp==3.16.2',
        ],
    }
    for k in ['0.11']
}
MAP_VERSION_TO_INSTALL_SEABORN.update(
    {
        k: {
            'python': '3.9',
            'install': 'python -m pip install -e .[dev]',
            'pip_packages': [
                'contourpy==1.1.0',
                'cycler==0.11.0',
                'fonttools==4.42.1',
                'importlib-resources==6.0.1',
                'kiwisolver==1.4.5',
                'matplotlib==3.7.2',
                'numpy==1.25.2',
                'packaging==23.1',
                'pandas==2.0.0',
                'pillow==10.0.0',
                'pyparsing==3.0.9',
                'pytest',
                'python-dateutil==2.8.2',
                'pytz==2023.3.post1',
                'scipy==1.11.2',
                'six==1.16.0',
                'tzdata==2023.1',
                'zipp==3.16.2',
            ],
        }
        for k in ['0.12', '0.13']
    }
)
MAP_VERSION_TO_INSTALL_PYTEST = {
    k: {'python': '3.9', 'install': 'python -m pip install -e .'}
    for k in [
        '4.4',
        '4.5',
        '4.6',
        '5.0',
        '5.1',
        '5.2',
        '5.3',
        '5.4',
        '6.0',
        '6.2',
        '6.3',
        '7.0',
        '7.1',
        '7.2',
        '7.4',
        '8.0',
    ]
}
MAP_VERSION_TO_INSTALL_PYTEST['4.4']['pip_packages'] = [
    'atomicwrites==1.4.1',
    'attrs==23.1.0',
    'more-itertools==10.1.0',
    'pluggy==0.13.1',
    'py==1.11.0',
    'setuptools==68.0.0',
    'six==1.16.0',
]
MAP_VERSION_TO_INSTALL_PYTEST['4.5']['pip_packages'] = [
    'atomicwrites==1.4.1',
    'attrs==23.1.0',
    'more-itertools==10.1.0',
    'pluggy==0.11.0',
    'py==1.11.0',
    'setuptools==68.0.0',
    'six==1.16.0',
    'wcwidth==0.2.6',
]
MAP_VERSION_TO_INSTALL_PYTEST['4.6']['pip_packages'] = [
    'atomicwrites==1.4.1',
    'attrs==23.1.0',
    'more-itertools==10.1.0',
    'packaging==23.1',
    'pluggy==0.13.1',
    'py==1.11.0',
    'six==1.16.0',
    'wcwidth==0.2.6',
]
for k in ['5.0', '5.1', '5.2']:
    MAP_VERSION_TO_INSTALL_PYTEST[k]['pip_packages'] = [
        'atomicwrites==1.4.1',
        'attrs==23.1.0',
        'more-itertools==10.1.0',
        'packaging==23.1',
        'pluggy==0.13.1',
        'py==1.11.0',
        'wcwidth==0.2.6',
    ]
MAP_VERSION_TO_INSTALL_PYTEST['5.3']['pip_packages'] = [
    'attrs==23.1.0',
    'more-itertools==10.1.0',
    'packaging==23.1',
    'pluggy==0.13.1',
    'py==1.11.0',
    'wcwidth==0.2.6',
]
MAP_VERSION_TO_INSTALL_PYTEST['5.4']['pip_packages'] = [
    'py==1.11.0',
    'packaging==23.1',
    'attrs==23.1.0',
    'more-itertools==10.1.0',
    'pluggy==0.13.1',
]
MAP_VERSION_TO_INSTALL_PYTEST['6.0']['pip_packages'] = [
    'attrs==23.1.0',
    'iniconfig==2.0.0',
    'more-itertools==10.1.0',
    'packaging==23.1',
    'pluggy==0.13.1',
    'py==1.11.0',
    'toml==0.10.2',
]
for k in ['6.2', '6.3']:
    MAP_VERSION_TO_INSTALL_PYTEST[k]['pip_packages'] = [
        'attrs==23.1.0',
        'iniconfig==2.0.0',
        'packaging==23.1',
        'pluggy==0.13.1',
        'py==1.11.0',
        'toml==0.10.2',
    ]
MAP_VERSION_TO_INSTALL_PYTEST['7.0']['pip_packages'] = [
    'attrs==23.1.0',
    'iniconfig==2.0.0',
    'packaging==23.1',
    'pluggy==0.13.1',
    'py==1.11.0',
]
for k in ['7.1', '7.2']:
    MAP_VERSION_TO_INSTALL_PYTEST[k]['pip_packages'] = [
        'attrs==23.1.0',
        'iniconfig==2.0.0',
        'packaging==23.1',
        'pluggy==0.13.1',
        'py==1.11.0',
        'tomli==2.0.1',
    ]
MAP_VERSION_TO_INSTALL_PYTEST['7.4']['pip_packages'] = [
    'iniconfig==2.0.0',
    'packaging==23.1',
    'pluggy==1.3.0',
    'exceptiongroup==1.1.3',
    'tomli==2.0.1',
]
MAP_VERSION_TO_INSTALL_PYTEST['8.0']['pip_packages'] = [
    'iniconfig==2.0.0',
    'packaging==23.1',
    'pluggy==1.3.0',
    'exceptiongroup==1.1.3',
    'tomli==2.0.1',
]
MAP_VERSION_TO_INSTALL_MATPLOTLIB = {
    k: {
        'python': '3.11',
        'packages': 'environment.yml',
        'install': 'python -m pip install -e .',
        'pre_install': [
            'apt-get -y update && apt-get -y upgrade && apt-get install -y imagemagick ffmpeg texlive texlive-latex-extra texlive-fonts-recommended texlive-xetex texlive-luatex cm-super dvipng'
        ],
        'pip_packages': [
            'contourpy==1.1.0',
            'cycler==0.11.0',
            'fonttools==4.42.1',
            'ghostscript',
            'kiwisolver==1.4.5',
            'numpy==1.25.2',
            'packaging==23.1',
            'pillow==10.0.0',
            'pikepdf',
            'pyparsing==3.0.9',
            'python-dateutil==2.8.2',
            'six==1.16.0',
            'setuptools==68.1.2',
            'setuptools-scm==7.1.0',
            'typing-extensions==4.7.1',
        ],
    }
    for k in ['3.5', '3.6', '3.7']
}
MAP_VERSION_TO_INSTALL_MATPLOTLIB.update(
    {
        k: {
            'python': '3.8',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
            'pre_install': [
                'apt-get -y update && apt-get -y upgrade && apt-get install -y imagemagick ffmpeg libfreetype6-dev pkg-config texlive texlive-latex-extra texlive-fonts-recommended texlive-xetex texlive-luatex cm-super'
            ],
            'pip_packages': ['pytest', 'ipython'],
        }
        for k in ['3.1', '3.2', '3.3', '3.4']
    }
)
MAP_VERSION_TO_INSTALL_MATPLOTLIB.update(
    {
        k: {
            'python': '3.7',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
            'pre_install': [
                'apt-get -y update && apt-get -y upgrade && apt-get install -y imagemagick ffmpeg libfreetype6-dev pkg-config'
            ],
            'pip_packages': ['pytest'],
        }
        for k in ['3.0']
    }
)
MAP_VERSION_TO_INSTALL_MATPLOTLIB.update(
    {
        k: {
            'python': '3.5',
            'install': 'python setup.py build; python setup.py install',
            'pre_install': [
                'apt-get -y update && apt-get -y upgrade && && apt-get install -y imagemagick ffmpeg'
            ],
            'pip_packages': ['pytest'],
            'execute_test_as_nonroot': True,
        }
        for k in ['2.0', '2.1', '2.2', '1.0', '1.1', '1.2', '1.3', '1.4', '1.5']
    }
)
MAP_VERSION_TO_INSTALL_SPHINX = {
    k: {
        'python': '3.9',
        'pip_packages': ['tox==4.16.0', 'tox-current-env==0.0.11'],
        'install': 'python -m pip install -e .[test]',
        'pre_install': ["sed -i 's/pytest/pytest -rA/' tox.ini"],
    }
    for k in ['1.5', '1.6', '1.7', '1.8', '2.0', '2.1', '2.2', '2.3', '2.4', '3.0']
    + ['3.1', '3.2', '3.3', '3.4', '3.5', '4.0', '4.1', '4.2', '4.3', '4.4']
    + ['4.5', '5.0', '5.1', '5.2', '5.3', '6.0', '6.2', '7.0', '7.1', '7.2']
}
for k in ['3.0', '3.1', '3.2', '3.3', '3.4', '3.5', '4.0', '4.1', '4.2', '4.3', '4.4']:
    MAP_VERSION_TO_INSTALL_SPHINX[k]['pre_install'].extend(
        [
            "sed -i 's/Jinja2>=2.3/Jinja2<3.0/' setup.py",
            "sed -i 's/sphinxcontrib-applehelp/sphinxcontrib-applehelp<=1.0.7/' setup.py",
            "sed -i 's/sphinxcontrib-devhelp/sphinxcontrib-devhelp<=1.0.5/' setup.py",
            "sed -i 's/sphinxcontrib-qthelp/sphinxcontrib-qthelp<=1.0.6/' setup.py",
            "sed -i 's/alabaster>=0.7,<0.8/alabaster>=0.7,<0.7.12/' setup.py",
            "sed -i \"s/'packaging',/'packaging', 'markupsafe<=2.0.1',/\" setup.py",
        ]
    )
    if k in ['4.2', '4.3', '4.4']:
        MAP_VERSION_TO_INSTALL_SPHINX[k]['pre_install'].extend(
            [
                "sed -i 's/sphinxcontrib-htmlhelp>=2.0.0/sphinxcontrib-htmlhelp>=2.0.0,<=2.0.4/' setup.py",
                "sed -i 's/sphinxcontrib-serializinghtml>=1.1.5/sphinxcontrib-serializinghtml>=1.1.5,<=1.1.9/' setup.py",
            ]
        )
    elif k == '4.1':
        MAP_VERSION_TO_INSTALL_SPHINX[k]['pre_install'].extend(
            [
                (
                    "grep -q 'sphinxcontrib-htmlhelp>=2.0.0' setup.py && "
                    "sed -i 's/sphinxcontrib-htmlhelp>=2.0.0/sphinxcontrib-htmlhelp>=2.0.0,<=2.0.4/' setup.py || "
                    "sed -i 's/sphinxcontrib-htmlhelp/sphinxcontrib-htmlhelp<=2.0.4/' setup.py"
                ),
                (
                    "grep -q 'sphinxcontrib-serializinghtml>=1.1.5' setup.py && "
                    "sed -i 's/sphinxcontrib-serializinghtml>=1.1.5/sphinxcontrib-serializinghtml>=1.1.5,<=1.1.9/' setup.py || "
                    "sed -i 's/sphinxcontrib-serializinghtml/sphinxcontrib-serializinghtml<=1.1.9/' setup.py"
                ),
            ]
        )
    else:
        MAP_VERSION_TO_INSTALL_SPHINX[k]['pre_install'].extend(
            [
                "sed -i 's/sphinxcontrib-htmlhelp/sphinxcontrib-htmlhelp<=2.0.4/' setup.py",
                "sed -i 's/sphinxcontrib-serializinghtml/sphinxcontrib-serializinghtml<=1.1.9/' setup.py",
            ]
        )
MAP_VERSION_TO_INSTALL_SPHINX['7.2']['pre_install'] += [
    'apt-get update && apt-get install -y graphviz'
]
MAP_VERSION_TO_INSTALL_ASTROPY = {
    k: {
        'python': '3.9',
        'install': 'python -m pip install -e .[test] --verbose',
        'pip_packages': [
            'attrs==23.1.0',
            'exceptiongroup==1.1.3',
            'execnet==2.0.2',
            'hypothesis==6.82.6',
            'iniconfig==2.0.0',
            'numpy==1.25.2',
            'packaging==23.1',
            'pluggy==1.3.0',
            'psutil==5.9.5',
            'pyerfa==2.0.0.3',
            'pytest-arraydiff==0.5.0',
            'pytest-astropy-header==0.2.2',
            'pytest-astropy==0.10.0',
            'pytest-cov==4.1.0',
            'pytest-doctestplus==1.0.0',
            'pytest-filter-subpackage==0.1.2',
            'pytest-mock==3.11.1',
            'pytest-openfiles==0.5.0',
            'pytest-remotedata==0.4.0',
            'pytest-xdist==3.3.1',
            'pytest==7.4.0',
            'PyYAML==6.0.1',
            'setuptools==68.0.0',
            'sortedcontainers==2.4.0',
            'tomli==2.0.1',
        ],
    }
    for k in ['0.1', '0.2', '0.3', '0.4', '1.1', '1.2', '1.3', '3.0', '3.1', '3.2']
    + ['4.1', '4.2', '4.3', '5.0', '5.1', '5.2']
}
for k in ['4.1', '4.2', '4.3', '5.0', '5.1', '5.2']:
    MAP_VERSION_TO_INSTALL_ASTROPY[k]['pre_install'] = [
        'sed -i \'s/requires = \\["setuptools",/requires = \\["setuptools==68.0.0",/\' pyproject.toml'
    ]
MAP_VERSION_TO_INSTALL_SYMPY = {
    k: {
        'python': '3.9',
        'packages': 'mpmath flake8',
        'pip_packages': ['mpmath==1.3.0', 'flake8-comprehensions'],
        'install': 'python -m pip install -e .',
    }
    for k in ['0.7', '1.0', '1.1', '1.10', '1.11', '1.12', '1.2', '1.4', '1.5', '1.6']
    + ['1.7', '1.8', '1.9']
}
MAP_VERSION_TO_INSTALL_SYMPY.update(
    {
        k: {
            'python': '3.9',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
            'pip_packages': ['mpmath==1.3.0'],
        }
        for k in ['1.13']
    }
)
MAP_VERSION_TO_INSTALL_PYLINT = {
    k: {
        'python': '3.9',
        'packages': 'requirements.txt',
        'install': 'python -m pip install -e .',
    }
    for k in [
        '2.10',
        '2.11',
        '2.13',
        '2.14',
        '2.15',
        '2.16',
        '2.17',
        '2.8',
        '2.9',
        '3.0',
    ]
}
MAP_VERSION_TO_INSTALL_PYLINT['2.8']['pip_packages'] = ['pyenchant==3.2']
MAP_VERSION_TO_INSTALL_PYLINT['2.8']['pre_install'] = [
    'apt-get update && apt-get install -y libenchant-2-dev hunspell-en-us'
]
MAP_VERSION_TO_INSTALL_PYLINT.update(
    {
        k: {
            **MAP_VERSION_TO_INSTALL_PYLINT[k],
            'pip_packages': ['astroid==3.0.0a6', 'setuptools'],
        }
        for k in ['3.0']
    }
)

MAP_VERSION_TO_INSTALL_XARRAY = {
    k: {
        'python': '3.10',
        'packages': 'environment.yml',
        'install': 'python -m pip install -e .',
        'pip_packages': [
            'numpy==1.23.0',
            'packaging==23.1',
            'pandas==1.5.3',
            'pytest==7.4.0',
            'python-dateutil==2.8.2',
            'pytz==2023.3',
            'six==1.16.0',
            'scipy==1.11.1',
            'setuptools==68.0.0',
        ],
        'no_use_env': True,
    }
    for k in ['0.12', '0.18', '0.19', '0.20', '2022.03', '2022.06', '2022.09']
}

MAP_VERSION_TO_INSTALL_SQLFLUFF = {
    k: {
        'python': '3.9',
        'packages': 'requirements.txt',
        'install': 'python -m pip install -e .',
    }
    for k in [
        '0.10',
        '0.11',
        '0.12',
        '0.13',
        '0.4',
        '0.5',
        '0.6',
        '0.8',
        '0.9',
        '1.0',
        '1.1',
        '1.2',
        '1.3',
        '1.4',
        '2.0',
        '2.1',
        '2.2',
    ]
}
MAP_VERSION_TO_INSTALL_DBT_CORE = {
    k: {
        'python': '3.9',
        'packages': 'requirements.txt',
        'install': 'python -m pip install -e .',
    }
    for k in [
        '0.13',
        '0.14',
        '0.15',
        '0.16',
        '0.17',
        '0.18',
        '0.19',
        '0.20',
        '0.21',
        '1.0',
        '1.1',
        '1.2',
        '1.3',
        '1.4',
        '1.5',
        '1.6',
        '1.7',
    ]
}
MAP_VERSION_TO_INSTALL_PYVISTA = {
    k: {
        'python': '3.9',
        'install': 'python -m pip install -e .',
        'pip_packages': ['pytest'],
    }
    for k in ['0.20', '0.21', '0.22', '0.23']
}
MAP_VERSION_TO_INSTALL_PYVISTA.update(
    {
        k: {
            'python': '3.9',
            'packages': 'requirements.txt',
            'install': 'python -m pip install -e .',
            'pip_packages': ['pytest'],
        }
        for k in [
            '0.24',
            '0.25',
            '0.26',
            '0.27',
            '0.28',
            '0.29',
            '0.30',
            '0.31',
            '0.32',
            '0.33',
            '0.34',
            '0.35',
            '0.36',
            '0.37',
            '0.38',
            '0.39',
            '0.40',
            '0.41',
            '0.42',
            '0.43',
        ]
    }
)
MAP_VERSION_TO_INSTALL_ASTROID = {
    k: {
        'python': '3.9',
        'install': 'python -m pip install -e .',
        'pip_packages': ['pytest'],
    }
    for k in [
        '2.10',
        '2.12',
        '2.13',
        '2.14',
        '2.15',
        '2.16',
        '2.5',
        '2.6',
        '2.7',
        '2.8',
        '2.9',
        '3.0',
    ]
}
MAP_VERSION_TO_INSTALL_MARSHMALLOW = {
    k: {
        'python': '3.9',
        'install': "python -m pip install -e '.[dev]'",
    }
    for k in [
        '2.18',
        '2.19',
        '2.20',
        '3.0',
        '3.1',
        '3.10',
        '3.11',
        '3.12',
        '3.13',
        '3.15',
        '3.16',
        '3.19',
        '3.2',
        '3.4',
        '3.8',
        '3.9',
    ]
}
MAP_VERSION_TO_INSTALL_PVLIB = {
    k: {
        'python': '3.9',
        'install': 'python -m pip install -e .[all]',
        'packages': 'pandas scipy',
        'pip_packages': ['jupyter', 'ipython', 'matplotlib', 'pytest', 'flake8'],
    }
    for k in ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']
}
MAP_VERSION_TO_INSTALL_PYDICOM = {
    k: {'python': '3.6', 'install': 'python -m pip install -e .', 'packages': 'numpy'}
    for k in [
        '1.0',
        '1.1',
        '1.2',
        '1.3',
        '1.4',
        '2.0',
        '2.1',
        '2.2',
        '2.3',
        '2.4',
        '3.0',
    ]
}
MAP_VERSION_TO_INSTALL_PYDICOM.update(
    {k: {**MAP_VERSION_TO_INSTALL_PYDICOM[k], 'python': '3.8'} for k in ['1.4', '2.0']}
)
MAP_VERSION_TO_INSTALL_PYDICOM.update(
    {k: {**MAP_VERSION_TO_INSTALL_PYDICOM[k], 'python': '3.9'} for k in ['2.1', '2.2']}
)
MAP_VERSION_TO_INSTALL_PYDICOM.update(
    {k: {**MAP_VERSION_TO_INSTALL_PYDICOM[k], 'python': '3.10'} for k in ['2.3']}
)
MAP_VERSION_TO_INSTALL_PYDICOM.update(
    {k: {**MAP_VERSION_TO_INSTALL_PYDICOM[k], 'python': '3.11'} for k in ['2.4', '3.0']}
)
MAP_VERSION_TO_INSTALL_HUMANEVAL = {k: {'python': '3.9'} for k in ['1.0']}
MAP_VERSION_TO_INSTALL_HUMANEVAL_FIX = {
    k: {'python': '3.10', 'packages': 'pytest'} for k in ['0.0.1']
}

# Constants - Task Instance Instllation Environment
MAP_VERSION_TO_INSTALL = {
    'astropy/astropy': MAP_VERSION_TO_INSTALL_ASTROPY,
    'dbt-labs/dbt-core': MAP_VERSION_TO_INSTALL_DBT_CORE,
    'django/django': MAP_VERSION_TO_INSTALL_DJANGO,
    'matplotlib/matplotlib': MAP_VERSION_TO_INSTALL_MATPLOTLIB,
    'marshmallow-code/marshmallow': MAP_VERSION_TO_INSTALL_MARSHMALLOW,
    'mwaskom/seaborn': MAP_VERSION_TO_INSTALL_SEABORN,
    'pallets/flask': MAP_VERSION_TO_INSTALL_FLASK,
    'psf/requests': MAP_VERSION_TO_INSTALL_REQUESTS,
    'pvlib/pvlib-python': MAP_VERSION_TO_INSTALL_PVLIB,
    'pydata/xarray': MAP_VERSION_TO_INSTALL_XARRAY,
    'pydicom/pydicom': MAP_VERSION_TO_INSTALL_PYDICOM,
    'pylint-dev/astroid': MAP_VERSION_TO_INSTALL_ASTROID,
    'pylint-dev/pylint': MAP_VERSION_TO_INSTALL_PYLINT,
    'pytest-dev/pytest': MAP_VERSION_TO_INSTALL_PYTEST,
    'pyvista/pyvista': MAP_VERSION_TO_INSTALL_PYVISTA,
    'scikit-learn/scikit-learn': MAP_VERSION_TO_INSTALL_SKLEARN,
    'sphinx-doc/sphinx': MAP_VERSION_TO_INSTALL_SPHINX,
    'sqlfluff/sqlfluff': MAP_VERSION_TO_INSTALL_SQLFLUFF,
    'swe-bench/humaneval': MAP_VERSION_TO_INSTALL_HUMANEVAL,
    'nielstron/humaneval_fix': MAP_VERSION_TO_INSTALL_HUMANEVAL_FIX,
    'sympy/sympy': MAP_VERSION_TO_INSTALL_SYMPY,
}

# Constants - Repository Specific Installation Instructions
MAP_REPO_TO_INSTALL = {}

# Constants - Task Instance Test Frameworks
TEST_PYTEST_VERBOSE = 'pytest -rA --tb=long -p no:cacheprovider'
MAP_REPO_TO_TEST_FRAMEWORK_VERBOSE = {
    'astropy/astropy': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_ASTROPY.keys()
    },
    'django/django': {
        k: './tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1'
        for k in MAP_VERSION_TO_INSTALL_DJANGO.keys()
    },
    'marshmallow-code/marshmallow': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_MARSHMALLOW.keys()
    },
    'matplotlib/matplotlib': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_MATPLOTLIB.keys()
    },
    'mwaskom/seaborn': {
        k: 'pytest -rA --tb=long' for k in MAP_VERSION_TO_INSTALL_SEABORN.keys()
    },
    'pallets/flask': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_FLASK.keys()
    },
    'psf/requests': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_REQUESTS.keys()
    },
    'pvlib/pvlib-python': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_PVLIB.keys()
    },
    'pydata/xarray': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_XARRAY.keys()
    },
    'pydicom/pydicom': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_PYDICOM.keys()
    },
    'pylint-dev/astroid': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_ASTROID.keys()
    },
    'pylint-dev/pylint': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_PYLINT.keys()
    },
    'pytest-dev/pytest': {
        k: 'pytest -rA --tb=long' for k in MAP_VERSION_TO_INSTALL_PYTEST.keys()
    },
    'pyvista/pyvista': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_PYVISTA.keys()
    },
    'scikit-learn/scikit-learn': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_SKLEARN.keys()
    },
    'sphinx-doc/sphinx': {
        k: 'tox -epy39 -v --' for k in MAP_VERSION_TO_INSTALL_SPHINX.keys()
    },
    'sqlfluff/sqlfluff': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_SQLFLUFF.keys()
    },
    'swe-bench/humaneval': {
        k: 'python' for k in MAP_VERSION_TO_INSTALL_HUMANEVAL.keys()
    },
    'nielstron/humaneval_fix': {
        k: TEST_PYTEST_VERBOSE for k in MAP_VERSION_TO_INSTALL_HUMANEVAL.keys()
    },
    'sympy/sympy': {
        k: 'bin/test -C --verbose' for k in MAP_VERSION_TO_INSTALL_SYMPY.keys()
    },
}
MAP_REPO_TO_TEST_FRAMEWORK_VERBOSE['django/django']['1.9'] = (
    './tests/runtests.py --verbosity 2'
)
