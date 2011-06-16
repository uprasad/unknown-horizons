# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import copy_reg
import multiprocessing
import os
import sys
import types
from optparse import OptionParser

# Allow instance methods to be pickled

def _pickle_method(method):
	func_name = method.im_func.__name__
	obj = method.im_self
	cls = method.im_class
	return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
	for cls in cls.mro():
		try:
			func = cls.__dict__[func_name]
		except KeyError:
			pass
		else:
			break
	return func.__get__(obj, cls)

copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)


class Simulation(object):
	"""
	Interface for all simulations.
	"""

	# List of tuples, defining the case. First element of each case has to be a
	# unique identifier.
	cases = []

	def set_config(self, output_dir, iterations, tick_interval):
		self.output_dir = output_dir
		self.iterations = iterations
		self.tick_interval = tick_interval

	def run(self, case):
		"""
		Runs the given case. Results need to be stored on disk (self.output_dir),
		no data may be set on the class.
		"""
		raise NotImplementedError

	def analyze_results(self):
		"""
		Do whatever you want with the data in self.output_dir.
		"""
		raise NotImplementedError


def get_simulation(filename):
	"""
	Get the simulation from the module given by its filename.

	Temporarly adds the base directory of the path to sys.path and
	import the module.
	"""
	directory, module_name = os.path.split(filename)
	module_name = os.path.splitext(module_name)[0]

	path = list(sys.path)
	sys.path.insert(0, directory)
	try:
		module = __import__(module_name)
	except:
		raise Exception("Module '%s' not found." % filename)
	finally:
		sys.path[:] = path

	return module.simulation


def run(args):
	parser = OptionParser("usage: %prog [options] path_to_simulation output_dir")
	parser.add_option("--worker", dest="worker", default=multiprocessing.cpu_count(),
		type="int", help="Number of processes to use [%default]")
	parser.add_option("--iterations", dest="iterations", default=200,
		type="int", help="[%default]")
	parser.add_option("--tick_interval", dest="tick_interval", default=40,
		type="int", help="[%default]")

	(options, args) = parser.parse_args(args=args)
	if len(args) != 2:
		parser.error("You need to specify a output directory and simulation.")

	simulation = get_simulation(args[0])
	simulation.set_config(args[1], options.iterations, options.tick_interval)
		
	if options.worker == 1:
		for case in simulation.cases:
			simulation.run(case)
	else:
		pool = multiprocessing.Pool(options.worker)
		pool.map(simulation.run, simulation.cases)

	simulation.analyze_results()

