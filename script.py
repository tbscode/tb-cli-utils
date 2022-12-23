#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# EXAMPLE for tb-cli-utils

import os
import cliutils
from cliutils import *


def get_parser(use_argcomplete=False):
    # autocompletion shouldn't show aliases that is why we pass `use_argcomplete`
    parser = get_default_parser(use_argcomplete)
    parser.add_argument("-env", "--environment")
    return parser


cliutils.get_parser = get_parser


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
    SCRIPT_NAME = args.quick_args.script_name \
        if args.quick_args.script_name else os.path.basename(__file__)
    subprocess.run(
        f"""bash --rcfile <(echo '. ~/.bashrc; eval "$(register-python-argcomplete {SCRIPT_NAME})" ')""",
        executable='/bin/bash',
        shell=True, env=os.environ)


@register_action(parser=quick_parser([Q_Opt(s1="-ex", s2="--example")]), own_args=True)
def example_parse_extra_args(args):
    print("---->",
          "Simple example using actions quick args:",
          "--example", "=", f"'{args.quick_args.example}'")


@register_action(alias=["k8"])
def kubectl(args):
    subprocess.run(["kubectl", *args.unparsed, "-n", "default-namespace"], env={
        "KUBE_CONFIG": "/this/projects/kube/config",
        "AUTH_DATA": "authprovider.get_auth()"
    })


if __name__ == "__main__":
    parse_actions_run()
