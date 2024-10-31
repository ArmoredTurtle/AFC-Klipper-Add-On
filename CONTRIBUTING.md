# Contributing

## Virtual environment

It is recommended to set up a python virtual environment to keep installed dependencies isolated from your system dependencies.

You can do this by running the following:

```shell
# Install virtualenv globally
pip install virtualenv

# Create local virtual environment (will create directory named "venv" in your working directory)
python3 -m venv venv

# Activate the virtual environment in your current terminal/shell
source venv/bin/activate
```

## Install dependencies

```shell
pip install -r requirements.txt
```

> [!NOTE]
> Klipper aims to be dependency free. We are ONLY using dependencies here for the development environment.
> We should not use any of these dependencies in any of the code that we intend to run in klipper.

### Klipper sources

This is not strictly required, but it can be helpful for your IDE (specifically tested with VSCode) to include the klipper
sources in your `PYTHONPATH`. To do this, at this time you'll need to manually clone klipper into this project like this:

```shell
git clone --depth=1 https://github.com/Klipper3d/klipper
```

Then you'll need to ensure the `klipper/klippy` is added in the `PYTHONPATH` environment variable. The project `.vscode/settings.json`
should configure that for VSCode, but you may need to refer to your own IDE for help ensuring the extra path is added.

## Linting

```shell
ruff check
```

> [!TIP]
> Some lint errors may be automatically fixable. Run `ruff check --fix` to fix them.

## Updating `requirements.txt`

If you need to add additional development tools (e.g. `pip install <some-dependency>`) that are to be used
by CI/CD workflows, ensure they are added to the `requirements.txt` by running the following:

```shell
pip freeze > requirements.txt
```

> [!WARNING]
> Ensure this is only done from a virtual environment, otherwise it will add all of your globally installed
> dependencies.
