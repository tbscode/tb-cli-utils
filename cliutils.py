"""
Tim's cli utils, 
this is to quickly build cli utils for managing a buch of relatively independent tasks.

the basic idea is that there are a few general '--' params and a buch of actions, 
every action parase its own params.

general syntax:

```shell
./script.py (-c context) [action] [params of action] (-a --b [args of action])
```

tasks an easily defined by adding the `@register_action` decorator

```python
e.g.:
@register_action(alias=["k8", "kubectl"], parse_own_args=True)
def autenticated_kubectl(args):
    subprocess.run(["kubectl", **args.unparsed, "-n", "default-namespace"], env={
        "KUBE_CONFIG" : "/this/projects/kube/config",
        "AUTH_DATA" : authprovider.get_auth()
    })
```

Now you can simply run `./script.py k8 get pods` without switching kube context or namespace.
You could e.g.: have a encryped database as authprovider and could simply require the password for that on every call.

Then you never have unencrypted credential.

These utils also prvide some basic general commands e.g.:

- `./script.py _help` generates help message based on doc-string for actions
- `./script.py _autocomplete` gives instructions on enabling autocompletion! ( even possible for actions )
- `./script.py _null_subprocess` this will supress all subproess calls and only print the commands

"""
import sys
import argparse
from typing import Optional, Callable
from dataclasses import dataclass
from functools import partial, wraps
from copy import deepcopy
import builtins as __builtin__
import subprocess


def get_default_parser():

    parser = argparse.ArgumentParser()
    default_actions = ["help"]
    parser.add_argument('actions', metavar='A', type=str, default=default_actions,
                        choices=get_all_action_names(), nargs='*', help='action')
    return parser


def get_parser():  # OVERWRITE if you wan custom default arguments!
    return get_default_parser()


ACTIONS = []  # Populated with the `@register_action` decorator
GLOBAL_PARSER = get_parser()


@dataclass
class ActionObj:
    # the fuction that should be executed ( you can also add a labmda if you need preprocessing )
    exec: Optional[Callable]
    # aliases for the action
    alias: list = []
    # Name for action ( set to function name if None )
    name: Optional[str] = None
    # continue executing after action
    cont: bool = True
    # If the action should be executed without STDOUT ( only cli-utils.print_force() will be allowed for output )
    silent: bool = False
    # If the action parses its own args
    own_args: bool = False


def manual_register_action(f, **_kwargs):
    _kwargs["name"] = _kwargs.get("name", f.__name__)
    ACTIONS.append(ActionObj(**_kwargs))

    @wraps(f)
    def run(*args, **kwargs):
        return f(*args, **kwargs)
    return run


def register_action(**kwargs):
    return partial(manual_register_action, **kwargs)


def get_all_action_names():
    return [a.name for a in ACTIONS]


@register_action(name="_help", alias=["?"])
def _print_help(a):
    print(__doc__)
    GLOBAL_PARSER.print_help()
    for act in ACTIONS:
        print(
            f"action '{act.name}' (with aliases {', '.join(act.alias)})")
        if act.exec:
            info = act.exec.__doc__
            print(f"\tinfo: {info}\n")
        else:
            print("\tNo info availabol")


def get_action_by_alias(alias) -> ActionObj:
    for a in ACTIONS:
        if alias in [a.name, *a.alias]:
            return a
    raise Exception(f"Action {alias} doesnt exist")


def parse_actions_run():
    def parse_args(_partial=None):
        if _partial:
            a = get_parser().parse_args(_partial)
        else:
            a = get_parser().parse_args()
        assert getattr(a, "actions") and a.actions
        return a
    a, _ = get_parser().parse_known_args()
    reparse = (None, False)
    for action in a.actions:
        act = get_action_by_alias(action)
        if act.own_args:
            reparse = (action, True)
    if reparse[1]:
        assert isinstance(reparse[0], str)
        _partial = sys.argv[1:sys.argv.index(reparse[0])+1]
        a = parse_args(_partial)
        setattr(a, 'unparsed', sys.argv[sys.argv.index(reparse[0]) + 1:])
    else:
        a = parse_args()
        setattr(a, 'unparsed', [])

    def read_unparsed(a):
        _u = a.unparsed
        a.unparsed = []
        return _u
    setattr(a, 'read_unparsed', read_unparsed)

    for action in a.actions if isinstance(a.actions, list) else [a.actions]:
        act = get_action_by_alias(action)
        assert act.exec, "No exec method defined"
        act.exec(a)

        if not act.cont:
            print(f"Ran into final action '{act.name}'")
            break
    if len(a.unparsed) > 1:
        print("there where unhandled extra args: " + " ".join(a.unknown))
    if not a.silent:
        print("Script finished!")
