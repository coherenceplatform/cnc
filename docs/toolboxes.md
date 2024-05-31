# Toolboxes

A `toolbox` is a way to run a command against a `cnc`-managed environment.

## Usage

```
# dev is the environment name in environment.yml
cnc toolbox start dev
```

You can also run a command and exit:

```
# dev is the environment name in environment.yml
cnc toolbox run dev --service backend python myscript.py
```

Will run `python myscript.py` in your built container for the `backend` service in the `dev` environment, including all the right environment variables. The container will be pulled from the registry in your cloud if it is not present on the machine running `cnc`.