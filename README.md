Flaunch | FBuild
================

Launch, build, and deployment management - brought to you by the makers of Flux.

# Launch
We have a lot of packages that we deal with in the world of VFX (a _lot_) and because of that - we have to handle a _lot_ of different environments, settings, tools, plugins, words, engines, pets, people, coffee mugs, you freakin name it.

Because of this crazy world - we have made a great stride to improve the way we handle composing these environments to make it clean and simple for users to launch what they need, when they need it.

Let's take running an app

```
~$> flaunch Flux
```

This will automatically start the latest version of Flux for us. It will download and manage the package all on it's own. Any requirements Flux needs are built into the package itself for which flaunch will gather and download in stride.

## Package in a Package...

When we pull down packages, we may have to obtain packages that they require. What's more is this process can recurse further and further untill all packages are loaded.

```
~$> flaunch --package PyFlux Helios -s /my/files.####.exr
```

The above command will grab `PyFlux` from our repository and prep our environment to use it, and then launch `Helios`. The python interpreter within `Helios` will have complete access to `PyFlux` without having to install it manually in any way.

## Running Direct Commands

`flaunch` can run direct commands within and environment as well with the `--run` flag

```
~$> flaunch -p MyAPI -p PyFluxMyStudio --run python /my/script.py
```

You'll notice we used multiple root packages with the short form of `--package` which is just `-p`. This can be used an unlimited number of times.

# Build
This is better left to some of the more formal [Documentation](doc/buildyaml.md).

# Compose
Let's say we want to turn something fugly like:

```
~$> flaunch -p PackageA:PackageB/1.23.4:AnotherPackage SomeApp --arg1 --arg2
```

Into something beautiful like:

```
~$> flaunch SomeAppWithArgs
```

This is where `fbuild compose` comes into play. It's a simple way to build a complex launcher program without lifting another finger.

```
~$> fbuild compose SomeAppWithArgs 1.0.0 \
    --package PackageA --package PackageB/1.23.4 --package AnotherPackage \
    --env 
    --launch SomeApp \
    --args --arg1 --arg2
```

That's it! `fbuild` will automatically register the package with Atom under the version `1.0.0` and give it the proper requirements and use the `"based_on"` `launch.json` arg for proper 

# Update
The `flaunch` suite will eventually need an upgrade. To make this process as painless as possible, we've added the ability to update the package at anytime with the simple command:

```
~$> fupdate
```

This command uses the same process as `flaunch` to detect is a newer package for `flaunch` exists within our repository and, if so, utilizes the files to upgrade itself.
