Creating fbuild files
=====================

The `fbuild` command helps merge the worlds of building a package with testing it in a multi-facet environment.

At the heart of this technology is the `build.yaml` files and our utility of them.

Rather than creating complicated python build scripts for everything or handling much of the same code over and over again, we use a simple yaml file that can handle both simple file organization as well as complicated builds and post process procedures.

# Starting Out

## The Pacakge
Let's say we have the follow package structure:

```
MyPackge
    `- MyPackage
        `- __init__py
```

And inside the `__init__.py` file, we have the following:

```py
import decimal  # default python lib

def dollars_from_cents(cents):
    decimal.getcontext().prec = 2
    return decimal.Decimal(0.01) * descimal.Decimal(cents)
```

Now we want to hook it up to `flaunch` for use with other packages and applications. To do so, let's create a `build.yaml` file on the top directory.

## The build.yaml

```yaml
# build.yaml

name: MyPackage # The name of our package

build:
  type: basic
```

> That's the absolute minimum build.yaml file there is. Odds are you'll be creating one with a bit more complexity.

So our structure should look like this:

```
MyPackage
    `- MyPackage/
    `- build.yaml
```

Once we have that, and we're looking to build our package, we head to the command line. Do use `fbuild` you'll want to set the following environment variables:

```
export FLAUNCH_BUILD_DIR=<default location you want to build packages>`
export FLAUNCH_DEV_DIR=<default location your source files exist in (e.g. your local git repo)>
```

In this case, `FLAUNCH_DEV_DIR` will be set to the directory above the _root_ `MyPackage`.

These two can be overwritten by the `fbuild` command but for now, with them set, we can build our package.

> Note: Make sure you have the flaunch and fbuild location added to your PATH environment variable otherwise the cli may not work.

```
fbuild MyPackage
```

With that we get a bit of information:

```
[28/05/2019 01:30:59 PM - INFO]: Build Path: C:/repo/build/MyPackage
[28/05/2019 01:30:59 PM - INFO]: Create Build Directory...
[28/05/2019 01:30:59 PM - INFO]: Copying Files...
[28/05/2019 01:30:59 PM - WARNING]: launch.json file not found! Expect issues when launching!
[28/05/2019 01:32:11 PM - INFO]: Build Complete
```

This tells us that the build completed! You should be able to find the build files within the `FLAUNCH_BUILD_DIR` you defined earlier.

## launch.json

You may have noticed the `WARNING` we received while building. The `launch.json` file wasn't included within our package and so `flaunch` won't be able to use it.

A `launch.json` file describes how we interact with a package. Some things this file handles:

* Listing other packages this package relies on
* Prepping an environment
* Executable path for using the `launch` command

We'll get into more details of the `launch.json` soon, but for now, let's get one in our package for use.

At this point you have two options:

1. Add a `launch.json` file to the root of your package
2. Add a `launch_json` argument to the build section of the `build.yaml` file.

For the second option, your build.yaml might look like the following:

```yaml
name: MyPackage

build:
  type: basic

  #
  # Basic dictionary that will map to our launch.json
  #
  launch_json:
    env:
        PATH: ["{path}"]
```

With this, we run `fbuild MyPackage` and we shouldn't see the `WARNING` anymore. You'll also notice that a `launch.json` file was created for you in the build directory with the `"env"` key.

> Tip: Use `fbuild -v <package>` to see all debug information

## Run our build
What's the point of building it if we can't actually use it? Let's give the python interpreter a shot.

```
flaunch env MyPackage/dev run python
```

Now you should have a python interpreter running from which you can use your package freely.

### Mixed Python Paths!

> Note/Tip/Warning: It's sometimes a good idea to try running the flaunch command from outside the source files to make sure you python interpreter isn't using your current working directory by default 

Once you have the interpreter running you should be able to run something like:

```python
>>> from MyPackage import dollars_from_cents
>>> print (dollars_from_cents(1000))
10.0
>>>
```

Now we have a (re)build-able environment that we can modify, build out of source, and test with it!

# Intermediate Tutorial
Now that we have some of the basics down, we can start to dig into the extra features...
