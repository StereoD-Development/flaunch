# Deployment and Release

## What is Deployment?
To `fbuild`, deployment is the process of propagating files to a server or globally for possible testing, consumption via development tools, or general requirements.

## What _isn't_ Deployment?
"Deployed" files are simply available at a file system level but **_not_** explicitly available to a typical user. `flaunch` uses Flux's back end to understand what files are available at any given time and because of this, we can deploy files safely without worry that users may be pulling them out of turn or before other, dependent, components are released.

## What is Release?
Release is the act of actually making the product available to the end user by alerting Flux's back end that it's ready for consumption. Because Flux is replicated, all users will gain access to the functionality at nearly the same time and there is no need to move any files once "released".

## How Does it Work?
`fbuild` handles global deployment through the transfer service provided by development as well as some identifiers in the `build.yaml`

# Stages
The deployment/release process happens in three distinct stages.

```
|`````````````````` Predeploy `````````````````|```````` Deploy ```````|````` Release `````|
 Local Build --> Package --> Predeploy Location --> Deployment Location --> [Flux Alerted]
```

# Predeploy
This stage acts as the intermediary between build files and deployment. We do a good chunk of validation here as well as package the built files into a `flaunch` consumable package.

# Basic Example
Let's take the `MyPackage` example we made in the [build docs](buildyaml.md).


Let's run a predeploy only command:
```
~$> fbuild deploy -v MyPackage 0.0.2
[02/07/2019 04:50:18 PM - DEBUG]: Starting Command...
[02/07/2019 04:50:18 PM - DEBUG]: Command: deploy
[02/07/2019 04:50:19 PM - DEBUG]: :Pre Deploy:
[02/07/2019 04:50:19 PM - DEBUG]:     Start Pre Execution...
[02/07/2019 04:50:19 PM - DEBUG]:     FUNC(install_path_to_predeploy(0.0.2))
[02/07/2019 04:50:19 PM - DEBUG]:         SET(MyPackage.0.0.2.zip package_zip)
[02/07/2019 04:50:19 PM - DEBUG]:         FUNC(get_complete_files_path())
[02/07/2019 04:50:19 PM - DEBUG]:             SET(-g C:/repo/build/MyPackage complete_files)
[02/07/2019 04:50:19 PM - DEBUG]:             Evaluating: prop_set('install_path')
[02/07/2019 04:50:19 PM - DEBUG]:         Evaluating: file_exists("//isilon2/s3d/resources/sw/temp/flux_predeploy/MyPackage/Windows/0.0.2/MyPackage.0.0.2.zip")
[02/07/2019 11:06:03 AM - DEBUG]:         ZIP(MyPackage.0.0.2.zip -f C:/repo/MyPackage/* -n)
[02/07/2019 11:06:03 AM - INFO ]:             Zipping: C:/repo/MyPackage/MyPackage/__init__.py
[02/07/2019 11:06:17 AM - INFO ]:             Zipping: C:/repo/MyPackage/launch.json
# ...
[02/07/2019 11:06:59 AM - DEBUG]:         MOVE(--make-dirs MyPackage.0.0.2.zip D:/s3d/resources/sw/temp/flux_predeploy/MyPackage/...)
[02/07/2019 11:06:59 AM - INFO ]:             Moving: MyPackage.0.0.2.zip -> D:/s3d/resources/sw/temp/flux_predeploy/MyPackage/Windows/0.0.2/
[02/07/2019 11:06:59 AM - DEBUG]:         SET(-g D:/s3d/resources/sw/temp/flux_predeploy/MyPackage/... deployable_files)
# ...
[02/07/2019 04:50:19 PM - INFO ]: Predeploy Only
[02/07/2019 04:50:19 PM - INFO ]: Deployment Complete
```

The following has occurred:

* Verify that files don't already exist
* Asserts that, if this is an installable app, that the right files are packaged
* Creates the zip package required for flaunch
* Moves the package to the predeploy location

# Deploy
To get this into proper deployment position and transfer it around the world, we add the `--transfer` flag. This will:

```
~$> fbuild deploy -v MyPackage 0.0.2 --transfer
```

* Copy package from predeploy to the final deployment location at the current facility
* Ship requests to have it moved around the world

## Existing Predeploy
If you have already predeployed the files and don't want/need to do it again, you can provide `--use-existing` to use it.

Alternatively, you can use `--force` to recreate the package completely in the predeploy location.

# Release
Once we have `MyPackage` on all supported platforms built and deployed, we can finally tell Flux about it.

```
~$> fbuild release MyPackage 0.0.2
[02/07/2019 05:11:52 PM - INFO ]: Registration Complete
```

Once complete, you can run the released package with a simple `flaunch` command

```
~$> flaunch -p MyPackage --run python
```

## Beta
Sometimes we want to send out a package but not make it the production release. This is useful for testing, back compatibility work, and other edge cases.

```
~$> fbuild release MyPackage 0.0.2 --beta
```

That will create an entry and let users launch explicitly (`flaunch -p MyPackage/0.0.2 ...`) but won't change the currently live release.

This can be combined and used in tandem like a "Release Candidate" procedure (might require the `--force` flag)
