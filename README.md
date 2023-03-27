depwalker
------

A simple dumb script to parse Debian packages file.

This script ignores the architecture restriction (`pkg:arch`) and version restriction (`pkg (>= 1.2.3)`).

Logic
------

It parses every packages in Debian's `Packages` file, then try to find the dependencies listed in the packages, one by one.

When finding dependencies, it will do the following:

- Find the given name in the main list, which consits of all parsed packages.
- Find the given name in the provided list, which consists of all names occurred in `Provides` field of a package.
- If all above fails, it will create a stub package, flag it as not available. Packages listed in stub list have high possibility not being able to install, i.e. apt will complain "Not installable" for such package.


Usage
------

```
./depwalker.py /path/to/combined/Packages/file
```

The “combined Packages file” consists of:
- Packages file for one architecture
- Packages file for `any` arch
- If target distro has multiple “suites”, you may have to combine them together.
You can create this file by:

```sh
cat Packages_all Packages_arch > Packages_combined
# Or, if your distro has multiple suites:
cat Packages_main_all Packages_main_arch Packages_contrib_all Packages_contrib_arch ... > Packages_combined
```