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

import os
import subprocess
from itertools import product

from horizons.command.building import Build
from horizons.command.unit import CreateUnit
from horizons.constants import UNITS, WILD_ANIMAL, BUILDINGS, RES
from horizons.entities import Entities

from tests.game import new_session, new_settlement
from tests.simulation import Simulation


class WildAnimalsHunter(Simulation):
	cases = [
		('0_hunter', 70, 2, 4, 50, 0),
		('2_hunter', 70, 2, 4, 50, 2),
		('4_hunter', 70, 2, 4, 50, 4),
	]

	def run(self, case):
		try:
			WILD_ANIMAL.HEALTH_LEVEL_TO_REPRODUCE = case[1]
			WILD_ANIMAL.HEALTH_DECREASE_ON_NO_JOB = case[2]
			WILD_ANIMAL.HEALTH_INCREASE_ON_FEEDING = case[3]
			WILD_ANIMAL.HEALTH_INIT_VALUE = case[4]
			hunter_count = case[5]
			
			session, player = new_session(rng_seed=42)
			settlement, island = new_settlement(session)
			settlement.inventory.alter(RES.GOLD_ID, 5000)
			settlement.inventory.alter(4, 500)
			settlement.inventory.alter(6, 500)

			# Populate island with trees and wild animals.
			Tree = Entities.buildings[BUILDINGS.TREE_CLASS]
			for coords, tile in sorted(island.ground_map.iteritems()):
				# add tree to every nth tile
				if session.random.randint(0, 2) == 0 and \
				   Tree.check_build(session, tile, check_settlement=False):
					building = Build(Tree, coords[0], coords[1], ownerless=True,island=island)(issuer=None)
					building.finish_production_now() # make trees big and fill their inventory
					if session.random.randint(0, 10) == 0: # add animal to every nth tree
						CreateUnit(island.worldid, UNITS.WILD_ANIMAL_CLASS, *coords)(issuer=None)

			hunters = []
			for (x, y) in product([25, 35], repeat=2):
				if len(hunters) == hunter_count:
					break
				building = Build(9, x, y, island, settlement=settlement)(issuer=player)
				assert building
				hunters.append(building)

			# Run the simulation.
			with open(os.path.join(self.output_dir, 'data_%s' % case[0]), 'w') as f:
				for i in range(self.iterations):
					f.write("%d\n" % len(island.wild_animals))
					[h.inventory._storage.clear() for h in hunters]
					session.run(ticks=self.tick_interval)

			session.end()
		except Exception as e:
			import sys
			import traceback
			print '*'*30
			print traceback.print_tb(sys.exc_info()[2])
			print '*'*30
			raise

	def analyze_results(self):
		data_filename = os.path.join(self.output_dir, 'data')
		datafiles = [open(os.path.join(self.output_dir, 'data_%s' % c[0]), 'r') for c in self.cases]

		with open(data_filename, 'w') as f:
			tick = 0
			for i in range(self.iterations):
				f.write("%d %s\n" % (tick, " ".join(v.strip() for v in map(file.readline, datafiles))))
				tick += self.tick_interval

		plots = []
		for i, case in enumerate(self.cases, start=2):
			plots.append('"%s" using 1:%d title "%s"' % (
				data_filename, i, case
			))
		plots = ','.join(plots)

		filename = os.path.join(self.output_dir, 'result.png')

		png_header ="""
			reset
			set term png size 1000, 800
			set output '%s'
		""" % filename

		script = """
			set xlabel "tick"
			set ylabel "count"

			set title "Wild animal population (20x20 island, 110 animals max)"
			set key on outside center bottom
			set grid
			set style data linespoints

			plot %s
		""" % plots

		with open(os.path.join(self.output_dir, 'plot.pg'), 'w') as f:
			f.write(png_header + script)

		with open(os.path.join(self.output_dir, 'plot_interactive.pg'), 'w') as f:
			f.write(script + "\npause -1")

		plot = subprocess.Popen(['gnuplot'], stdin=subprocess.PIPE)
		plot.communicate(png_header + script)


simulation = WildAnimalsHunter()
