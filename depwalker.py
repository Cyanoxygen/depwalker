#!/usr/bin/env python3
# depwalker - Stats of packages
import re
import os
import sys
import argparse
from typing import *
all_deps = False


class Package:
	def __init__(self, name: str, arch: str, deps: list, prov: list, is_avail: bool = True) -> None:
		self.name = name
		self.deps = deps
		self.arch = arch
		self.prov = prov
		is_avail = is_avail
	def __repr__(self) -> str:
		return '[Package {}: {}]'.format(self.name, self.arch)

# Global variables are great, isn't it?
packages: List[Package] = []
packages_dict: dict[str, Package] = {}
packages_prov_dict: dict[str, Package] = {}
stub_packages_list: dict[str, Package] = {}

def read_Packages_file(filename):
	"""
	Reads the `Packages` file, split into respective packages, then parse them.
	"""
	with open(filename, 'r', encoding='utf-8') as package_file:
		raw_package_content: str = ''
		while True:
			line = package_file.readline()
			# Empty string means we are at EOF.
			if line == '':
				break
			# Packages are split by an empty line.
			if line != "\n":
				raw_package_content += line
				continue
			# We hit a blank line, parse the package.
			parse_package(raw_package_content)
			raw_package_content = ''

def parse_pkglist(pkgs) -> list[str]:
	'''
	Split package list in Depends, Conflicts, and other fields into a list.
	Versoin restrictions will be removed.
	'''
	list_pkgs = list(x.strip() for x in pkgs.split(','))
	list_pkgs = list(re.sub(r'\(.*?\)', '', x).strip() for x in list_pkgs)
	
	# Find if there are multiple dependencies exist
	for item in list_pkgs:
		if '|' in item:
			# print("Found optional dependencies: {}".format(item))
			# split them into list items.
			optional_deps_list = list(x.strip() for x in item.split('|'))

			if not all_deps:
				# Replace the string with splitted list.
				list_pkgs[list_pkgs.index(item)] = optional_deps_list
				# print("Optional dependencies splitted: {}".format(list_pkgs))
			else:
				index = list_pkgs.index(item)
				concat = list_pkgs[0:index - 1]
				concat.extend(optional_deps_list)
				concat.extend(list_pkgs[index + 1:])
				list_pkgs.clear()
				list_pkgs.extend(concat)
	# Remove duplicates
	return dict.fromkeys(list_pkgs, None).keys() if all_deps else list_pkgs


def parse_package(content: str):
	# print("Parsing package!")
	pkg_dict: dict[str, str] = {}
	lastkey = ''
	for line in content.splitlines():
		if not line.startswith(' '):
			k, v = line.split(':', 1)
			lastkey = k
			pkg_dict[k.strip()] = v.strip()
		else:
			pkg_dict[lastkey] += ' '.join(line.strip())
	# Now we have a basic structure, but we need to process them further, i.e. `Depends` field. 
	# `Depends` field is a list of packages, showing its dependency, we need to remove the version restrictions, and convert it into a list.
	# Todo done: add Optional() support.
	# TODO Add Provides.
	print(f"\033[2KParsed package: {pkg_dict['Package']}", end='\r')
	if 'Depends' in pkg_dict.keys():
		parsed_deps = parse_pkglist(pkg_dict['Depends'])
		pkg_dict['Depends'] = parsed_deps
	if 'Provides' in pkg_dict.keys():
		parsed_provs = parse_pkglist(pkg_dict['Provides'])
		pkg_dict['Provides'] = parsed_provs
	
	pkgobj = Package(pkg_dict['Package'], pkg_dict['Architecture'],
		[] if 'Depends' not in pkg_dict.keys() else pkg_dict['Depends'],
		[] if 'Provides' not in pkg_dict.keys() else pkg_dict['Provides'])

	packages.append(pkgobj)
	packages_dict[pkg_dict['Package']] = pkgobj
	for prov in pkgobj.prov:
		# print("\033[2KNote, adding `{}` provided by package `{}` to main package list".format(prov, pkgobj.name))
		packages_prov_dict[prov] = pkgobj
		


def build_dependency_tree(pkg: Package):
	"""
	Here comes the hard part. We need to build the dependency tree, for every packages.
	The algorithm is simple. Lookup the list of dependencies, and try to find them, and assign them back.
	"""
	if pkg.deps == None:
		return
	print("\033[2KBuilding the dependency tree of {}...".format(pkg.name), end='\r')
	got_deps: list[Package] = []
	for dep in pkg.deps:
		if type(dep) is str:
			if ':' in dep:
				continue
			if dep in packages_dict.keys():
				got_deps.append(packages_dict[dep])
			elif dep in packages_prov_dict.keys():
				got_deps.append(packages_prov_dict[dep])
			else:
				# raise KeyError("Unable to find the dependency `{}` of package `{}` !".format(dep, pkg.name))
				print('\033[2KNote, dependency `{}` which is depended by {}, is not presnt in current collection! Adding stub package.'.format(dep, pkg.name))
				stubpkg = Package(dep, 'any', [], [], False)
				if dep not in stub_packages_list.keys():
					stub_packages_list[dep] = stubpkg
				got_deps.append(stub_packages_list[dep])

		elif type(dep) is list:
			found = False
			for inner_dep in dep:
				if ':' in inner_dep:
					continue
				if found:
					break
				if inner_dep in packages_dict.keys():
					found = True
					got_deps.append(packages_dict[inner_dep])
					break
				elif inner_dep in packages_prov_dict.keys():
					found = True
					got_deps.append(packages_prov_dict[inner_dep])
					break
			if not found:
				# No optional deps found. This is an error.
				# raise KeyError("Unable to find any of the packages described in '{}' of package '{}'".format(dep, pkg))
				print('\033[2KNote, dependency `{}` which depended by {}, is not presnt in current collection! Adding stub package.'.format(inner_dep, pkg.name))
				stubpkg = Package(inner_dep, 'any', [], [], False)
				if inner_dep not in stub_packages_list.keys():
					stub_packages_list[inner_dep] = stubpkg
				got_deps.append(stub_packages_list[inner_dep])
	# print(dep)
	pkg.deps = got_deps
				

def main():
	filename = sys.argv[1] if len(sys.argv) != 1 else "/home/cyan/temp/Packages4"
	print("[+] Parsing Packages file `{}`...".format(filename))
	read_Packages_file(filename=filename)
	print("\033[2K[+] Done parsing Packages.")
	print(f"[+] Parsed {len(packages)} packages in total.")
	print("[+] Building the dependency tree...")
	for pkgname in packages_dict:
		build_dependency_tree(packages_dict[pkgname])
	print("\033[2K[+] Done building dependency tree.")
	print("[+] We have {} packages in the main list.".format(len(packages_dict)))
	print("[+] We have {} packages provided by other package.".format(len(packages_prov_dict)))
	print("[+] We have {} stub packages in the main list.".format(len(stub_packages_list)))

if __name__ == '__main__':
	main()			



