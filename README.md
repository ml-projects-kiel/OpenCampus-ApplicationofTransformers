![Build-CI](https://github.com/ml-projects-kiel/OpenCampus-ApplicationofTransformers/actions/workflows/build_pipeline_CI.yaml/badge.svg) ![Build-CD](https://github.com/ml-projects-kiel/OpenCampus-ApplicationofTransformers/actions/workflows/build_pipeline_CD.yaml/badge.svg)

### Poetry

Poetry is a tool for dependency management and packaging in Python. It allows you to declare the libraries your project depends on and it will manage (install/update) them for you. [About Poetry](https://python-poetry.org/).

- Install Poetry
    | OS      | Command                                                                                                              |
    | ------- | -------------------------------------------------------------------------------------------------------------------- |
    | Windows | <code>(Invoke-WebRequest -Uri ht<span>tps://</span>install.python-poetry.org -UseBasicParsing).Content | py -</code> |
    | Mac     | <code>curl -sSL ht<span>tps://</span>install.python-poetry.org | python3 -</code>                                    |

- After installing poetry restart terminal/cmd <br>

- Activate installed Python >=3.9 from Pyenv in Poetry:<br>
    `poetry env use /full/path/to/python`

- (Optional) Config Poetry venv inside the repository:<br>
    `poetry config virtualenvs.in-project true`

- After cloning the repo (go inside the repo), you create and activate a venv via:<br>
    `poetry shell`

- The installations of all libraries will be done via:<br>
    `poetry install`
