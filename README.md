# napari-findaureus

[![License MIT](https://img.shields.io/pypi/l/napari-findaureus.svg?color=green)](https://github.com/githubuser/napari-findaureus/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-findaureus.svg?color=green)](https://pypi.org/project/napari-findaureus)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-findaureus.svg?color=green)](https://python.org)
[![tests](https://github.com/githubuser/napari-findaureus/workflows/tests/badge.svg)](https://github.com/githubuser/napari-findaureus/actions)
[![codecov](https://codecov.io/gh/githubuser/napari-findaureus/branch/main/graph/badge.svg)](https://codecov.io/gh/githubuser/napari-findaureus)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-findaureus)](https://napari-hub.org/plugins/napari-findaureus)

"Findaureus" is now available to use in napari.

Findaureus is a tool designed to identify bacteria in infected bone tissue images obtained via Confocal Laser Scanning Microscopy (CLSM). This tool can be accessed independently here. Recently, Findaureus has been integrated as a plugin for napari. In addition to its bacteria-locating algorithm, the napari viewer provides improved visualization features, in 2D and 3D perspectives.

----------------------------------
## Installation
### Windows/Linux
If you don’t have conda installed, you can get miniconda or Anaconda from their websites.
1. Open your command line tool and run these commands to create and activate a conda environment:
```
conda create -n napari-findaureus python=3.9
conda activate napari-findaureus
```
2. Install napari and napari-findaureus with this command:
```
pip install "napari[all]" napari-findaureus
```
### Start napari-findaureus
Launch napari from the terminal while the napari-findaureus environment is running.
```
napari
```
To launch the napari plugin, go to “Plugins” and select “napari-findaureus”.
## Quick demo

## Contributing

## License

Distributed under the terms of the [MIT] license,
"napari-findaureus" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
