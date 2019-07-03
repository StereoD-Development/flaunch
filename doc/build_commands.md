Command Lists
=============

Another vital and powerful feature of `fbuild` is it's rich command tools. By abstracting some components into easy-to-use commands, while leaving the ability to run raw command line expressions, you can get the most out of the build technology without having to have a different build procedure for each platform.

# The Syntax
A Command List is, unsurprisingly, a list of commands that we want to execute. A "Command" in this context *isn't* just a command line operation but potentially a tree of possible code paths to follow.

## Basic Command
```
COMMAND_LIST = [ "<command>", ... ]
```

Let's start by just looking a simple set of commands:

```yaml
- "echo This is a Command"
- "echo Another command!"
```

Here, we run the first command, which pushes `"This is a Command"` to the stdout. Then, after completing that task, we move to the second which pushes the next command. All of this is as though you ran each command by hand in a terminal.

## Argument Conditional Commands

```
- [ "<required_argument>", COMMAND_LIST ]
```

Now, let's say we only wanted to run select commands when a select argument was passed to our command:

```yaml
- "echo I'll go no matter what!"
- [ "--some-arg",
    [
        "echo I'll need an arg to run!",
        "echo I too am just another Command List!"
    ]
  ]
```

This command will always print out `"I'll go no matter what!"` but, unless `--some-arg` is passed to the command line of `fbuild`, it's not going to happen!

## Clause Conditional Commands
```
- clause: <python_evaluated_clause>
  commands: COMMAND_LIST
```

This is a conditional execution that takes in a string an evaluates it to determine in the branch should be run. This is for basic checks only and cannot run full scripts (see the `:PYTHON` command for that).

```yaml
- clause: "env_set('MY_ENV_VARIABLE')"
  commands:
    - echo "That env was set"
    # ...
```

This command will use the provided function `"env_set()"` to determine if the environment variable has any value. If it does, then the command list within `commands` is run.

Currently, the provided functions are:

* `env_check(var, val)` : Check if an environment variable is set to a specific value
* `env_set(var)`: Check if an environment variable is set to anything
* `prop_set(var)`: Check if our `build.yaml` has a specific property set
* `file_exists(var)`: Check if a file at a given path exists

## Platform Routing
Because this is `build.yaml` - _any_ _time_ you want to route based on platform, you are allowed to do so. Command Lists are no exception.

```yaml
- "echo foo"
- windows:
    "echo I AM WINDOWS!"
  unix:
    "echo I AM _NOT_ WINDOWS!"
```

# FBuild Commands
```
:<COMAND_NAME> <COMMAND_ARG>...
```
On top of having access to your terminal from the build process, you have a small but mighty suite of additional commands at your disposal. For general actions like writing/reading from a file, to copying/moving files in a platform agnostic way.

What's more, is command plugins can be made to suit your pipelines specific needs should a problem present itself.

An FBuild Command is used by starting with a `:` and followed by the alias to the command itself.

```yaml

props:
  my_script: |
    x = "{version_information}"
    x = x.strip()
    if int(x[0]) >= 1:
        print ("Version is above 1!")

# ...
  commands:
    - ":READ C:/code/project/version.txt version_information"
    - ":PYTHON my_script"
    - ":PYTHON -f C:/code/project/another_script.py"
```

There's a lot going on there, but hopefully it's pretty straight forward.

1. We fill our `props:` with a python script using yaml's multi line notation (`|`)
2. Within the `commands:` of our process we have a few tasks
    1. `:READ` will read a file and push the contents of said file to a `prop:` so we can use it in later commands
    2. `:PYTHON` will execute python from a `prop:` variable that we've passed.
        * `my_script` is first expanded upon, which resolves the `{version_information}` variable within the code

To find documentation on all native commands you can run the following:

```
fbuild command --doc
```

### :PYTHON Command
When using the `:PYTHON` command and executing a `prop:`, should you need a `dict` or `set`, which would require `{}`, then you need only put a space anywhere inside of the brackets. The expansion will ignore any captures with spaces in them.

For example:
```
# ...
  my_script: |
    username = 'My Cool Name'
    x = '{username}'
```

This resolve to something like:
```python
usename = 'My Cool Name'
x = 'John Doe'
```

By simply adding a space:
```
# ...
  my_script: |
    username = 'My Cool Name'
    x = {username }
```
You will get the desired results. Odds are this will be a very rare occurrence but worth noting none the less.

### :SUPER Command
In the event we want to overload a proceedure or simple call another set of commands from a [template](buildyaml.md#a-template) we're overloading.

```
include:
  - some_package
build:
  # ...
  commands:
    - ":PRINT foo"
    - ":SUPER some_package.build.commands"
```

This is akin to python's `super()`

### :FUNC Command
A useful command for refining your build procedure and componentalizing (not a word) your toolkit.

You define a function on your `build.yaml` root with the `func__` prefix. Something like:
```yaml
func__my_function():
    # COMMAND_LIST
```

Then it's up to you what you want to do within that Command List. You can use all the same argument checking, clauses, etc. When you want to use it, simply call the `:FUNC` command

```
# ... Somewhere in a COMMAND_LIST
    - ":FUNC my_function()"
```

### :FUNC Arguments
With the latest version of `fbuild`, we've introduced arguments into functions.

You have the ability to provide through three interfaces.

1. Through `props:`
    * This is pretty straight forward and allows you to provide different values as needed
2. Through the cli
3. Through the function call itself

For the second/third option, things get really interesting, let's look at an example

```yaml
func__function_with_args(foo_bar, schmoo):
  - ":PRINT {foo_bar}"
  - ":PRINT {schmoo}"
```

Now that our function has arguments, we can supply them through the cli with a slight "converted" syntax. This systax simply prepends `--` and converts `_` to `-`. For the example above the arguments would look like:

```
~$> ... --foo-bar the_first_value --schmoo another_value
```

We also support simply passing the arguments as you would in any other language

```yaml
  #...
  commands:
    - ":SET {some_expansion}/{my_file}.zip blarg"
    - ":SET {some_expansion}/{my_file}.tar.gz blarg_two"
    - ":FUNC function_with_args({blarg}, {blarg_two})" # Will expand and map accordingly
```

### :RETURN Command
When working with COMMAND_LISTS and functions there may be a scenario where you need to return from the current scope

# Comand Expansion (... Notation)
Occasionally, we have to handle command line arguments in a list fashion. For example:

```yaml
props:
  some_arguments: '-t foo -vvv --another-arg "blarg bloog"'

# ...
  commands:
    - "mytool {some_arguments} {my_filename}.foo"
```

When running those commands, the terminal would recieve:
```
["mytool"] ["-t foo -vvv --another-arg \"blarg bloog\""] ["the_filename.foo"]
```

No sensible parser would be able to understand that. To help with this, while using a `COMMAND_LIST`, you can denote that you want to separate via an `shlex.split()`.

```
# ...
  commands:
    - "mytool {some_arguments...} {my_filename}.foo"
```

Which translates to:
```
["mytool"] ["-t"] ["foo"] ["-vvv"] ["--another-arg"] ["blarg bloog"] ["the_filename.foo"]
```

# Chaining Commands
With all of these concepts, and the power of the `build.yaml` including Variable Expansion and Platform Routing we can generate very potent commands to fit our needs.


```yaml
props:
  real_build_command:
    windows: mymake
    unix: unimake
  make_right_dirs: |
    import os
    for dir_suffix in ["one", "two", "three"]:
        fp = "{build_dir}/build_component_" + dir_suffix
        if not os.path.isdir(fp):
            oa.makedirs(fp)

# ...

build:
  type: basic

  pre_build:
    - [ "--clean-start", ":RM -r -f {build_dir}/*" ]
    - ":PYTHON make_right_dirs"

  commands:
    # We always build component one
    - ":CD {build_dir}/build_component_one"
    - "{real_build_command} {source_dir}/component_one/buildfile ."

    - windows:
        # Only build extra components on windows if the environment is set
        - clause: 'env_check("WINDOWS_BUILD_COMP_2", "True")'
          commands:
            - ":CD {build_dir}/build_component_two"
            - "{real_build_command} {source_dir}/component_two/buildfile ."

        - clause: 'env_check("WINDOWS_BUILD_COMP_3", "True")'
          commands:
            - ":CD {build_dir}/build_component_three"
            - "{real_build_command} {source_dir}/component_two/buildfile ."

      unix:
        # Unix doesn't currently build the extra components
        - ":PRINT Unix compatibility coming soon..."

```

This might look a little intense, but real world situations usually call for some pretty serious build strategies and the `build.yaml` is prepared to get the job done.
