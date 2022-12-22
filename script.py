#!/usr/bin/env python3
# EXAMPLE for tb-cli-utils

import os
import cliutils
from cliutils import *


def get_parser():
    parser = get_default_parser()
    parser.add_argument("-env", "--environment")
    argcomplete.autocomplete(parser)
    return parser


cliutils.get_parser = get_parser


@register_action(alias=["complete"])
def activate_completion(args):
    """
    I dont use argompletes global completion.
    This allowes you to simply dispatch into a bash session with completion enabled 
    """
    subprocess.run(
        f"""bash --rcfile <(echo '. ~/.bashrc; eval "$(register-python-argcomplete act.py)" ')""",
        executable='/bin/bash',
        shell=True, env=os.environ)


@register_action(alias=["k8"])
def kubectl(args):
    subprocess.run(["kubectl", *args.unparsed, "-n", "default-namespace"], env={
        "KUBE_CONFIG": "/this/projects/kube/config",
        "AUTH_DATA": "authprovider.get_auth()"
    })


if __name__ == "__main__":
    parse_actions_run()
