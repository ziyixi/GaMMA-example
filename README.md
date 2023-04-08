# GaMMA example

## Install
To install the package with the gloabl optimization option, run the following command in the terminal:
```
poetry install
```
Or install packages with pip with reference to the `pyproject.toml` file.

To install the package with the local optimization option, run the following command in the terminal:
```
poetry remove gmma
poetry add git+https://github.com/AI4EPS/GaMMA.git
```

## Usage
To run the example, run the following command in the terminal:
```
poetry run python test_gamma.py
```

## Note
The eikonal solver will be rerun when switching from the global option to the local option due to a bug in storing the time table in @Aaaapril4's version. It's not a critical one and will not influence the result. The bug will be fixed in the future.