![Build-CI](https://github.com/ml-projects-kiel/OpenCampus-ApplicationofTransformers/actions/workflows/build_pipeline_CI.yaml/badge.svg) ![Build-CD](https://github.com/ml-projects-kiel/OpenCampus-ApplicationofTransformers/actions/workflows/build_pipeline_CD.yaml/badge.svg)

# OpenCampus - Application of Transformers

## Installation

### Hugging Face + PyTorch

Using Hugging Face on MacOs requires the following dependency to be installed BEFORE the PyTorch installation.

- If the `libshm.dylib` file is missing, run:<br>
  `brew install libomp`

### Poetry

Poetry is a tool for dependency management and packaging in Python. It allows you to declare the libraries your project depends on and it will manage (install/update) them for you. [About Poetry](https://python-poetry.org/).

- Install Poetry
  | OS | Command |
  | ------- | -------------------------------------------------------------------------------------------------------------------- |
  | Windows | <code>(Invoke-WebRequest -Uri ht<span>tps://</span>install.python-poetry.org -UseBasicParsing).Content \| py -</code> |
  | Mac | <code>curl -sSL ht<span>tps://</span>install.python-poetry.org \| python3 -</code> |

- After installing poetry restart terminal/cmd <br>

- (Optional) Config Poetry venv inside the repository:<br>
  `poetry config virtualenvs.in-project true`

- Create the venv with Python >=3.10:<br>
  `poetry env use /full/path/to/python`

- After creating the venv restart the shell:<br>
  `poetry shell`

- The installations of all libraries can be done via:<br>
  `poetry install`

  - (Optional) The dependencies are separated into groups. Groups can be included and excluded:<br>
    `poetry install --without Group1,Group2` or `poetry install --with Group1,Group2`<br>
    More info can be found [here](https://python-poetry.org/docs/cli/#install).

- Install pre-commit yaml:<br>
  `pre-commit install`

### Development Setup

This Repo enforces some coding standards.

- Git settings:<br>
  `pull.rebase=true`

- VSCode settings:<br>
  ```
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "editor.formatOnSave": true,
    "files.trimTrailingWhitespace": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": [
        "--line-length",
        "100"
    ],
  ```
