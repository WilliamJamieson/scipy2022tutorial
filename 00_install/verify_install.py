#!/usr/bin/env python

"""
Check for required dependencies for the workshop.
Usage::

  python verify_install.py

"""

import importlib.metadata
import re
import sys
from pathlib import Path
from typing import Collection, Dict, Mapping

import yaml
from packaging.version import Version

with open(Path(__file__).parent / "environment.yml") as environment_file:
    environment = yaml.safe_load(environment_file)

DEPENDENCY_PATTERN = re.compile(r"([\w\d-]+)\s*((?:[<>=~]=?|\^)\s*[\d\w.]*)?")
MINIMUM_DEPENDENCY_PATTERN = re.compile(r".*>=?\s*([\d\w.]+).*")


def parse_dependency(
    dependency: str,
    version_specification_pattern: re.Pattern = DEPENDENCY_PATTERN,
) -> Dict[str, str]:
    parsed = {}
    if isinstance(dependency, str):
        match = re.match(version_specification_pattern, dependency)
        if match is not None:
            groups = match.groups()
            parsed.update({groups[0]: groups[1]})
    elif isinstance(dependency, Mapping):
        for subdependency in dependency.values():
            parsed.update(
                parse_dependency(subdependency, version_specification_pattern)
            )
    elif isinstance(dependency, Collection):
        for subdependency in dependency:
            parsed.update(
                parse_dependency(subdependency, version_specification_pattern)
            )
    return parsed


DEPENDENCIES = {}

for dependency in environment["dependencies"]:
    DEPENDENCIES.update(parse_dependency(dependency))

INSTALLED_PACKAGES = {
    distribution.metadata["name"].lower(): distribution.metadata["version"]
    for distribution in importlib.metadata.distributions()
}


def check_package(
    package_name: str, minimum_version: Version = None, verbose: bool = True
) -> bool:
    if package_name in INSTALLED_PACKAGES:
        installed_version = Version(INSTALLED_PACKAGES[package_name])
        if minimum_version is not None:
            if not isinstance(minimum_version, Version):
                minimum_version = Version(str(minimum_version))
            if installed_version < minimum_version:
                print(
                    f'"{package_name}" is installed ({installed_version}) '
                    f"but out of date ({minimum_version} required)",
                    file=sys.stderr,
                )
                return False
        if verbose:
            print(f'"{package_name}" is installed ({installed_version})')
    else:
        print(f'"{package_name}" is not installed', file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    errors = []
    for package_name, specification in DEPENDENCIES.items():
        if package_name not in ["python"]:
            if specification is not None:
                min_version = re.match(
                    MINIMUM_DEPENDENCY_PATTERN,
                    specification,
                )
                if min_version is not None:
                    min_version = Version(min_version.groups()[0])
            else:
                min_version = None
            if not check_package(package_name, minimum_version=min_version):
                errors.append(package_name)
    if any(errors):
        print(
            f"You must resolve {sum(errors)} errors (above) "
            f"before running the tutorials."
        )
        exit(1)
    else:
        print("Your Python environment is good to go!")
