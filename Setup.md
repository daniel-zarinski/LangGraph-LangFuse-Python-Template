# Install pyenv
[Pyenv Official Documentation](https://github.com/pyenv/pyenv)
```bash
brew install pyenv
```

## Install Project Specific Python Version
You must install the appropriate Python version as defined in `./python-version`. 
This must be done once and then pyenv will automatically switch to this version on load.
```bash
pyenv install 3.13
```

# Install Postgres Dependencies
```bash
brew install postgresql
```
Alternatively you can install the libpq directly and add it to your shell.

# Start Development Services
```bash
make docker-compose-up-services
```