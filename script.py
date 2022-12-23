#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# EXAMPLE for tb-cli-utils

import os
import cliutils
from cliutils import *

cliutils.SCRIPT_NAME = "./script.py"


def get_parser(use_argcomplete=False):
    """
    You can add elements to the default parser by overwriting get_parser()
    You can even vary the parser if scanned by argparse, by using the user_argcomplete param
    if you want to present a limited subset of choices for completion
    """
    parser = get_default_parser(use_argcomplete)
    parser.add_argument("-env", "--environment")
    return parser


cliutils.get_parser = get_parser


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
