#!/usr/bin/python
##
## @author Edouard DUPIN
##
## @copyright 2012, Edouard DUPIN, all right reserved
##
## @license APACHE v2.0 (see license file)
##

from lutin import debug
from lutin import target
from lutin import tools
import os
import stat
import re
from lutin import host
from lutin import multiprocess

class Target(target.Target):
	def __init__(self, config):
		#processor type selection (auto/arm/ppc/x86)
		if config["arch"] == "auto":
			config["arch"] = "x86"
		#bus size selection (auto/32/64)
		if config["bus-size"] == "auto":
			config["bus-size"] = str(host.BUS_SIZE)
		target.Target.__init__(self, "Pepper", config, "")
		#Overwride the based on version
		self.config_based_on = "Linux"
		
		if self.config["bus-size"] == "64":
			# 64 bits
			if host.BUS_SIZE != 64:
				self.add_flag("c", "-m64")
		else:
			# 32 bits
			if host.BUS_SIZE != 32:
				self.add_flag("c", "-m32")
		
		self.add_flag("c", "-fpic")
		
		self.pkg_path_data = "share"
		self.pkg_path_bin = "bin"
		self.pkg_path_lib = "lib"
		self.pkg_path_license = "license"
		
		self.base_path_toolchain = os.path.join(os.getenv("HOME"), ".local", "share", "qi", "toolchains", "atom")
		
		if self.config["compilator"] == "clang":
			debug.error("does not support clang compilator")
		else:
			base_path_atom = os.path.join(self.base_path_toolchain, "x-tools", "bin")
			self.set_cross_base(os.path.join(base_path_atom, "i686-aldebaran-linux-gnu-"))
			if not os.path.isdir(base_path_atom):
				debug.error("Gcc Atom path does not exist !!! : " + basepathAtom)
		
		self.global_sysroot = "--sysroot=" + os.path.join(self.base_path_toolchain, "x-tools", "i686-aldebaran-linux-gnu", "sysroot")
		
	
	"""
	.local/application
	    *--> applName -> applName.app/bin/applName
	    *--> applName.app
	        *--> appl_description.txt
	        *--> appl_name.txt
	        *--> changelog.txt
	        *--> copyright.txt
	        *--> readme.txt
	        *--> version.txt
	        *--> website.txt
	        *--> icon.png
	        *--> bin
	        *    *--> applName
	        *--> doc
	        *    *--> applName
	        *--> lib
	        *    *--> XX.so
	        *    *--> YY.so
	        *--> license
	        *    *--> applName.txt
	        *    *--> libXX.txt
	        *    *--> libYY.txt
	        *--> man
	        *--> share
	        *    *--> applName
	        *    *--> XX
	        *    *--> YY
	        *--> sources
	"""
	def make_package_binary(self, pkg_name, pkg_properties, base_pkg_path, heritage_list, static):
		debug.debug("------------------------------------------------------------------------")
		debug.info("-- Generate generic '" + pkg_name + "' v" + tools.version_to_string(pkg_properties["VERSION"]))
		debug.debug("------------------------------------------------------------------------")
		#output path
		target_outpath = os.path.join(self.get_staging_path(pkg_name), pkg_name + ".app")
		tools.create_directory_of_file(target_outpath)
		
		## Create share datas:
		self.make_package_binary_data(target_outpath, pkg_name, base_pkg_path, heritage_list, static)
		
		## copy binary files:
		self.make_package_binary_bin(target_outpath, pkg_name, base_pkg_path, heritage_list, static)
		
		## Create libraries:
		self.make_package_binary_lib(target_outpath, pkg_name, base_pkg_path, heritage_list, static)
		
		## Create generic files:
		self.make_package_generic_files(target_outpath, pkg_properties, pkg_name, base_pkg_path, heritage_list, static)
		
		## create the package:
		debug.debug("package : " + os.path.join(self.get_staging_path(pkg_name), pkg_name + ".app.pkg"))
		os.system("cd " + self.get_staging_path(pkg_name) + " ; tar -czf " + pkg_name + ".app.tar.gz " + pkg_name + ".app")
		#multiprocess.run_command("cd " + self.get_staging_path(pkg_name) + " ; tar -czf " + pkg_name + ".app.tar.gz " + pkg_name + ".app")
		tools.create_directory_of_file(self.get_final_path())
		tools.copy_file(os.path.join(self.get_staging_path(pkg_name), pkg_name + ".app.tar.gz"), os.path.join(self.get_final_path(), pkg_name + ".app.gpkg"))
	
	def install_package(self, pkg_name):
		debug.debug("------------------------------------------------------------------------")
		debug.info("-- Install package '" + pkg_name + "'")
		debug.debug("------------------------------------------------------------------------")
		# this is temporary ... Will call:
		if False:
			os.system("lutin-pkg -i " + os.path.join(self.get_final_path(), + pkg_name + ".app.gpkg"))
		else:
			#Copy directly from staging path:
			appl_path = os.path.join(self.get_staging_path(pkg_name), pkg_name + ".app")
			target_path = os.path.join(os.path.expanduser("~"), ".local", "application", pkg_name + ".app")
			target_bin_path = os.path.join(os.path.expanduser("~"), ".local", "application", pkg_name + ".app", "bin", pkg_name)
			target_bin_link = os.path.join(os.path.expanduser("~"), ".local", "application", pkg_name)
			# remove output path:
			tools.remove_path_and_sub_path(target_path)
			# remove executable link version:
			tools.remove_file(target_bin_link)
			# copy result:
			tools.copy_anything(appl_path, target_path, recursive=True)
			# create synbolic link:
			debug.info("kkk " + "ln -s " + target_bin_path + " " + target_bin_link)
			os.symlink(target_bin_path, target_bin_link)
	
	def un_install_package(self, pkg_name):
		debug.debug("------------------------------------------------------------------------")
		debug.info("-- Un-Install package '" + pkg_name + "'")
		debug.debug("------------------------------------------------------------------------")
		# this is temporary ... Will call:
		if False:
			os.system("lutin-pkg -r " + pkg_name)
		else:
			#Copy directly from staging path:
			target_path = os.path.join(os.path.expanduser("~"), ".local", "application", pkg_name + ".app")
			target_bin_link = os.path.join(os.path.expanduser("~"), ".local", "application", pkg_name)
			# remove output path:
			tools.remove_path_and_sub_path(target_path)
			# remove executable link version:
			tools.remove_file(target_bin_link)
	
	def run(self, pkg_name):
		debug.debug("------------------------------------------------------------------------")
		debug.info("-- Run package '" + pkg_name + "'")
		debug.debug("------------------------------------------------------------------------")
		appl_path = os.path.join(self.get_staging_path(pkg_name), pkg_name + ".app", "bin", pkg_name)
		multiprocess.run_command_no_lock_out(appl_path)
		debug.debug("------------------------------------------------------------------------")
		debug.info("-- Run package '" + pkg_name + "' Finished")
		debug.debug("------------------------------------------------------------------------")


