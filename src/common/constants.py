"""
Basic constants across the f<tool> ecosystem
"""

# -------------------------------------------
# -- Environment Variables
# -------------------------------------------

# -- Set by the developer:

# The default build directory to use when developing
# and constructing a package
FLAUNCH_BUILD_DIR   = 'FLAUNCH_BUILD_DIR'

# The default location to search for <package>/build.yaml
# files as well as the source materials
FLAUNCH_DEV_DIR     = 'FLAUNCH_DEV_DIR'

# --  Set by flaunch when running a command

# The package string that was used when calling the command
# e.g. PyFlux/dev:nkFluxMadrid
FLAUNCH_PACKAGES    = 'FLAUNCH_PACKAGES'

# The application (or execuable) we're running
# e.g. Flux | python.exe
FLAUNCH_APPLICATION = 'FLAUNCH_APPLICATION'

# The execution command that was used
# e.g. 'launch' | 'run'
FLAUNCH_EXEC        = 'FLAUNCH_EXEC'

# The arguments that were supplied to the FLAUNCH_APPLICATION
# e.g. --rpcurl=http://123.123.123.123/rpc/
FLAUNCH_ARGUMENTS   = 'FLAUNCH_ARGUMENTS'


# -------------------------------------------
# --
# -------------------------------------------
