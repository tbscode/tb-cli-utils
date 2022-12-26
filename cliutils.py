# tb's cli utils,
import os
import sys
import argparse
from typing import Optional, Callable
from dataclasses import dataclass, field
from functools import partial, wraps
from copy import deepcopy
import subprocess
import argcomplete

SCRIPT_NAME = None


def get_all_action_and_alias_names():
    aliases_and_names = []
    for a in ACTIONS:
        aliases_and_names += [a.name, *a.alias]
    return aliases_and_names


def get_all_action_names():
    return [a.name for a in ACTIONS]


def get_default_parser(use_argcomplete=False):

    parser = argparse.ArgumentParser()
    default_actions = ["help"]
    action_choices = get_all_action_names(
    ) if use_argcomplete else get_all_action_and_alias_names()
    parser.add_argument('actions', metavar='A', type=str, default=default_actions,
                        **(dict(choices=action_choices) if use_argcomplete else {}), nargs='*', help='action')
    return parser


@dataclass
class Q_Opt:
    s1: str = ""
    s2: str = ""
    choices: Optional[list] = None


def quick_parser(simple_args: 'list[Q_Opt]'):
    parser = argparse.ArgumentParser()
    for arg in simple_args:
        parser.add_argument(arg.s1, arg.s2,
                            **({'choices': arg.choices}
                               if arg.choices else {}))
    return parser


def get_parser(use_argcomplete=False):  # OVERWRITE if you wan custom default arguments!
    return get_default_parser()


ACTIONS = []  # Populated with the `@register_action` decorator


@dataclass
class ActionObj:
    # the fuction that should be executed ( you can also add a labmda if you need preprocessing )
    exec: Optional[Callable]
    # aliases for the action
    alias: list = field(default_factory=list)
    # Name for action ( set to function name if None )
    name: Optional[str] = None
    # continue executing after action
    cont: bool = True
    # If the action should be executed without STDOUT ( only cli-utils.print_force() will be allowed for output )
    silent: bool = False
    # If the action parses its own args
    own_args: bool = False
    # an optional parser ( if user wants autocompletion )
    parser: Optional[Callable] = None


def manual_register_action(f, **_kwargs):
    _kwargs["name"] = _kwargs.get("name", f.__name__)
    _kwargs["exec"] = _kwargs.get("exec", f)
    ACTIONS.append(ActionObj(**_kwargs))

    @wraps(f)
    def run(*args, **kwargs):
        return f(*args, **kwargs)
    return run


def register_action(**kwargs):
    return partial(manual_register_action, **kwargs)


@register_action(name="print_help", alias=["?"], own_args=True)
def help(a):
    if a.unparsed and "--markdown-table" in a.unparsed:
        # use `read_unparsed` when u used an argument
        # then the scipt wont warn about unused arguements
        a.read_unparsed(a, "--markdown-table")
        # this will try to generate a markdown table summarizing registered actions
        from pytablewriter import MarkdownTableWriter
        writer = MarkdownTableWriter(
            headers=["[action]", "aliases",
                     "__doc__", "parses own args"],
            value_matrix=[
                [act.name, act.alias, act.exec.__doc__, act.own_args] for act in ACTIONS
            ],
        )
        print(writer.dumps())
        return
    print(__doc__)
    get_parser().print_help()
    for act in ACTIONS:
        print(
            f"action '{act.name}' (with aliases {', '.join(act.alias)})")
        if act.exec:
            info = act.exec.__doc__
            print(f"\tinfo: {info}\n")
        else:
            print("\tNo doc string found")


@register_action(cont=True, alias=["_null_subprocess"])
def print_commands(args, extra_out=["C"]):
    """ 
    Supress all output from subprocess. (run / check_output / call)
    AND only print the commands being executed
    """
    def _print_command_and_args(*args, **kwargs):
        print(
            *extra_out, f"_cmd: `{' '.join(args[0]) if isinstance(args[0], list) else args[0]}`, kwargs: {kwargs}")

        class Placeholder:
            stdout = ''
        return Placeholder()
    subprocess.run = _print_command_and_args
    subprocess.check_output = _print_command_and_args
    subprocess.call = _print_command_and_args


def get_environment_as_dict(path: str) -> dict:
    with open(path, 'r') as f:
        return dict(tuple(line.replace('\n', '').split('=')) for line
                    in f.readlines() if not line.startswith('#'))


@register_action(alias=["activate_completion"],
                 parser=quick_parser(
                     [Q_Opt(s1="-sn", s2="--script-name")]),
                 own_args=True)
def complete(args):
    """
    If you dont use global completion then;
    this allowes you to simply dispatch into a bash session with completion enabled 
    example usage: `./script.py complete -sn script.py`
    """
    name = args.quick_args.script_name \
        if args.quick_args.script_name else SCRIPT_NAME
    command = f"""bash --rcfile <(echo '. ~/.bashrc; eval "$(register-python-argcomplete {name})" ')"""
    subprocess.run(command,
                   executable='/bin/bash',
                   shell=True, env=os.environ)


def get_action_by_alias(alias) -> ActionObj:
    for a in ACTIONS:
        if alias in [a.name, *a.alias]:
            return a
    raise Exception(f"Action {alias} doesnt exist")


def parse_actions_run():
    argcomplete.autocomplete(get_parser(use_argcomplete=False))

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
            break
    if reparse[1]:
        assert isinstance(reparse[0], str)
        _partial = sys.argv[1:sys.argv.index(reparse[0])+1]
        a = parse_args(_partial)
        setattr(a, 'unparsed', sys.argv[sys.argv.index(reparse[0]) + 1:])
    else:
        a = parse_args()
        setattr(a, 'unparsed', [])

    def read_unparsed(a, args):
        for _a in (args if isinstance(args, list) else [args]):
            if _a in a:
                delattr(a, _a)
    setattr(a, 'read_unparsed', read_unparsed)

    for action in a.actions if isinstance(a.actions, list) else [a.actions]:
        act = get_action_by_alias(action)
        assert act.exec, "No exec method defined"
        if act.parser is not None:
            a.quick_args, unkn = act.parser.parse_known_args()
            a.unparsed = unkn
        act.exec(a)

        if not act.cont:
            print(f"Ran into final action '{act.name}'")
            break
    if len(a.unparsed) > 1:
        print("there where unhandled extra args: " + " ".join(a.unparsed))
    print("Script finished!")
