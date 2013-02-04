# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

from fife.extensions.pychan.widgets import Container, Slider, Label, Icon
from fife.extensions.pychan.widgets.common import Attr, IntAttr

class StepSlider(Container):
	""" Slider which has fixed value and snaps to those.
		HACK/NOTE: You need to call widget.init_widget() from the game code.

		Set widget.callback from code to call function to update value display labels etc.
		@param steps ";" separated string of values
		@param scale_type 0: None, 1: Value labels, 2: Markers"""

	ATTRIBUTES = Container.ATTRIBUTES + [ Attr('steps'), IntAttr('scale_type') ]

	def __init__(self, steps=None, scale_type=1, callback=None, **kwargs):
		super(StepSlider, self).__init__(**kwargs)
		self.steps = steps
		self.scale_type = scale_type
		self.callback = callback

	def init_widget(self):
		#If user passes unkown scale_type value, assume No scale
		if self.scale_type not in (0, 1, 2):
			self.scale_type = 0

		slider_size = (self.size[0], self.size[1] if not self.scale_type else self.size[1]-15) #Make space for scale

		self.steps_list = []
		#Create dictionary containing slider indices with corresponding true values
		self.steps_list = sorted(float(step) for step in self.steps.split(";"))
		self.steps_dict = dict(zip(xrange(len(self.steps_list)), self.steps_list))

		number_of_steps = len(self.steps_list)

		# Create and add slider
		self.slider = Slider(name=self.name+"_slider",
							size=slider_size,
							position=(0,0),
							step_length=1.0,
							scale_start=0.0,
							scale_end=float(number_of_steps-1),
							is_focusable=0,
							orientation=0)
		self.addChild(self.slider)
		self.slider.capture(self._update_slider, "action")

		if self.scale_type:
			# Create and add the scale
			scale_size = (self.size[0], 15)
			scale_box = Container(name="scale_box",
							size=scale_size,
							position=(0,15))

			marker_position_raio = self.slider._getWidth() / (number_of_steps-1)
			for i in range(number_of_steps):
				name = str(i)
				if self.scale_type == 2:
					marker = Icon(name=name, image="content/gui/icons/widgets/slider_marker.png")
				else:
					marker = Label(name=name, text=unicode(str(self.steps_dict[i])))
					marker.resizeToContent()

				if i == 0:
					marker._setX(0)
				elif i == number_of_steps-1:
					marker._setX(scale_box.size[0]-marker.size[0])
				else:
					marker._setX((marker_position_raio*i)-(marker.size[0]/2))
				marker._setY(0)
				scale_box.addChild(marker)
			scale_box.adaptLayout()
			self.addChild(scale_box)

	def _get_steps(self):
		return self._steps

	def _set_steps(self, steps):
		self._steps = steps
	steps = property(_get_steps, _set_steps)

	def _get_scale_type(self):
		return self._scale_type

	def _set_scale_type(self, scale_type):
		self._scale_type = scale_type
	scale_type = property(_get_scale_type, _set_scale_type)

	def getData(self):
		#Return true value corresponding to current index
		return self.steps_dict[int(self.slider._getValue())]

	def setData(self, data):
		#Find and set value closest to user input which is valid in the list
		real_value = min(self.steps_list, key=lambda x:abs(x-float(data)))
		for index, value in self.steps_dict.iteritems():
			if value == real_value:
				self.slider._setValue(float(index))

	def _getValue(self):
		return self.getData()

	def _setValue(self, value):
		self.setData(value)
	value = property(_getValue, _setValue)

	def _update_slider(self, event):
		old_val = self.slider._getValue()
		new_val = round(self.slider._getValue()) #Value of nearest slider index
		self.slider._setValue(new_val) #Snap to nearest index
		if self.callback:
			self.callback()

