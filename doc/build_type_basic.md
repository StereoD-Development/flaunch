# type: basic
The simplest build type but also the most flexible. Be default it's just a copy machine for files in your source directory. This is usually enough for most development to take place.

When using the build type `basic`, you have the following options available to you:

* `use_gitignore: (bool)`: By default `fbuild` will search your source directory for a `.gitignore` file and utilize that for finding ignore patterns when copying files. If you want to forgo this behavior, set this to `false`


