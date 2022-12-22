### Tim's cli utils,

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

Then you never have unencrypted credentials laying around.

These utils also prvide some basic general commands e.g.:

- `./script.py _help` generates help message based on doc-string for actions
- `./script.py _null_subprocess` this will supress all subproess calls and only print the commands

- `./script.py _autocomplete` gives instructions on enabling autocompletion! ( even possible for actions )
  > ( added soon, only need to refactor old implementation )
