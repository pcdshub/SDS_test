import math
from epics import PV
import time

class Pump:
	# below are list of PVs being used
	PUMP = 'Run'
	MAX_PRESSURE = 'MaxPress'
	SET_MAX_PRESSURE = 'SetMaxPress'
	FLOW_RATE = 'FlowRateSP'
	SET_FLOW_RATE = 'SetFlowRate'
	PRESSURE = 'Pressure'
	STATUS = 'Status'
	CLEAR_ERROR = 'ClearError.PROC'

	def __init__(self, prefix, min_flow = '', max_flow = ''):
		self.prefix = prefix
		self.min_flow = min_flow
		self.max_flow = max_flow

	def get_pulsation(self, flow_rate):
		# flow rate unit ml/min
		self.flow_rate = flow_rate
		self.start_pump(1)
		# not reading values for about 5 seconds because it sometime takes a while to get the pressure up from 0
		time.sleep(10)
		read_pressure = []
		time_track = 0
		while True:
			read_pressure.append(self.pressure)
			time_track += 1
			time.sleep(0.95)
			# run pulsation test for 30 seconds
			if time_track >= 30:
				self.flow_rate = 0
				self.start_pump(0)
				break
		max_press_value = max(read_pressure)
		min_press_value = min(read_pressure)
		avg_press_value = (max_press_value + min_press_value) / 2
		return (max_press_value - avg_press_value) / avg_press_value * 100

	def start_pump(self, todo):
		# todo should be 1 if you want to turn it on
		# todo should be 0 if you want to turn it off
		on_off = PV(self.prefix + self.PUMP)
		on_off.put(todo)

	def status(self):
		# 0 -> pump ready, 1 -> pump running
		# 3, 4 -> pump error
		status = PV(self.prefix + self.STATUS)
		return status.get()

	def clear_error(self):
		clear = PV(self.prefix + self.CLEAR_ERROR)
		# TODO find out how this PV works and update to clear error
		clear.put(1)

	@property
	def pressure(self):
		pressure = PV(self.prefix + self.PRESSURE)
		return pressure.get()

	@property
	def max_pressure(self):
		max_pressure_value = PV(self.prefix + self.MAX_PRESSURE)
		return max_pressure_value.get()

	@max_pressure.setter
	def max_pressure(self, max_pressure_input):
		set_max_pressure_to = PV(self.prefix + self.SET_MAX_PRESSURE)
		set_max_pressure_to.put(max_pressure_input)

	@property
	def flow_rate(self):
		flow_rate_value = PV(self.prefix + self.FLOW_RATE)
		return flow_rate_value.get()

	@flow_rate.setter
	def flow_rate(self, flow_rate_input):
		set_flow_rate_to = PV(self.prefix + self.SET_FLOW_RATE)
		set_flow_rate_to.put(flow_rate_input)

# # Object test code
# p = Pump('TST:LC20:SDS:')
# print(p.MAX_PRESSURE)
# print(p.max_pressure)
# p.max_pressure = 100
# print(p.max_pressure)


class Port:
	def __init__(self, port_number, pressure, flow_rate):
		self.port_number = port_number
		self.pressure = pressure
		self.flow_rate = flow_rate
		
	def display_info(self):
		return "Port#: %d; Pressure: %f; Flowrate: %f" %(self.port_number, self.pressure, self.flow_rate)


# # Port object test code
# port1 = Port(1, 2.2, 3.3)
# print(port1.display_info())
# Port.pressure = 222
# print(Port.pressure)
# print(port1.display_info())


class Tube:
	VOLUME_UNIT = 'uL'
	DIAMETER_UNIT = 'um'
	LENGTH_UNIT = 'cm'

	def __init__(self, color = '', outer_diameter ='', inner_diameter = '', length = '', material = ''):
		self.material = material
		self.outer_diameter = outer_diameter
		self.inner_diameter = inner_diameter
		self.length = length
		self.color = color

	def calculate_volume(self):
		return ((math.pi*(self.inner_diameter/2)**2)*(self.length*10000)) # the /10000 is to convert the length form centimeter to microns

	def cross_section_area(self):
		return ((math.pi*(self.inner_diameter/2)**2))
		# area in um squared

	def display_tube_description(self):
		return 'Color:\t %s\n\
				Material:\t %s\n\
				Outer diameter:\t %.4f %s\n\
				Inner diameter:\t %.4f %s\n\
				Length:\t %.4f %s\n\
				Volume:\t %.4f %s'\
				%(self.color, self.material, float(self.outer_diameter), self.DIAMETER_UNIT, \
						float(self.inner_diameter), self.DIAMETER_UNIT, float(self.length), self.LENGTH_UNIT, float(self.calculate_volume()), self.VOLUME_UNIT)

# # Tube Object Test Code
# waterTube = Tube('Black', 2500, 500, 10, 'peek')
# sampleTube = Tube('Red', 2500, 127, 10, 'peek' )
# fakeTube = Tube('Blue', 2500, 250, 10, 'peek' )

# print(waterTube.display_tube_description())
# print(fakeTube.display_tube_description())
# print(sampleTube.display_tube_description())


class Actuator(object):
	def __init__(self, prefix, suffix, serial_number = '00000000', times_rebuilt=0, times_used=0, number_of_ports=12):
		# by default uses port number 1
		# suffix of PV of port number
		self.prefix = prefix
		self.suffix = suffix
		self.serial_number = serial_number
		self.times_rebuilt = times_rebuilt
		self.times_used = times_used
		self.number_of_ports = number_of_ports
		self.active_port = PV(self.prefix + self.suffix).get()

	def goto_port(self, destination_port):
		self.active_port = destination_port
		PV(self.prefix + self.suffix).put(self.active_port)

	def increment_port(self):
		self.active_port += 1
		PV(self.prefix + self.suffix).put(self.active_port)

	def decrement_port(self):
		self.active_port -= 1
		PV(self.prefix + self.suffix).put(self.active_port)

	def display_info(self):
		print ('Serial number: ' , self.serial_number)
		# print ('Times this valve has been rebuilt: ', self.times_rebuilt)
		# print ('Times this valve has been used: ', self.times_used)
		print ('Number of ports: ', self.number_of_ports)
		print ('Active Port: ', self.active_port)

# Object Test Code
# a1 = Actuator('TST:SDS:SEL2:', '12T-7764V')
# a1.display_info()
# import pdb; pdb.set_trace()
# a1.goto_port(6)
# a1.display_info()


class ControlModule:    
	def __init__(self, vendor, module):
		self.vendor = vendor
		self.module = module
		
	def display_info(self):
		return 'Vendor: %s\nModule: %s' %(self.vendor, self.module)
	   
		
		
# ### OBJECT TEST CODE
# mod1 = ControlModule('Beckhofff', 'EP1111-0000')
# print mod1.display_info()


class Meter(object):
	
	def __init__(self, minimum = 0, maximum = 10, value = 0):
		self.min_scale = minimum
		self.max_scale = maximum
		self.value = value
		
	def read_meter(self):
		return 'Meter Reading: %f' %(self.value) 
		
			
class FlowMeter(Meter):
	def __init__(self, prefix, vendor = '', model = '', *args, **kwargs):
		self.prefix = prefix
		self.vendor = vendor
		self.model = model
		super(FlowMeter, self).__init__(*args, **kwargs)
		
	def read_info(self):
		return 'vendor: %s; Model: %s' %(self.vendor, self.model)

	def reset_flow_integrator(self, suffix):
		reset = PV(self.prefix + suffix)
		reset.put(0)

	def get_volume_used(self, suffix):
		volume_used = PV(self.prefix + suffix)
		return volume_used.get()

	# reset_flow_integrator and get_volume_used has same suffix



	
# ### Object test code
# dvm = FlowMeter('Sensirion', 'SLG-0075')
# print(dvm.read_meter())
# # dvm.set_value(8.3)
	
# print(dvm.read_info())
# print(dvm.read_meter())