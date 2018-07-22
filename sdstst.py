import datetime
import time
import sys, select
import pandas as pd
import matplotlib.pyplot as plt
from sample_delivery_system import *
from functions import *
import logging
import matplotlib.pyplot as plt
plt.style.use('seaborn-white')

# create logger
level = logging.INFO
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers = [logging.FileHandler('SDS_test.log'), logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers)
logger = logging.getLogger(__name__)

# # TODO ask user for prefix / macros. or set them based on selector box and pump version if possible
# prefix_sel_box = input('enter the prefix that is being used for selector box')
prefix_sel_box = 'TST:SDS:SEL2:'
# prefix_pump = input('enter the prefix that is being used for the pump')
prefix_pump = 'TST:LC20:SDS:'

# object initializations
Pump = Pump(prefix_pump)
FlowMeter = FlowMeter(prefix_sel_box)
# water
Actuator1 = Actuator(prefix_sel_box, 'VLV:01:RES_REQ')
# sample
Actuator2 = Actuator(prefix_sel_box, 'VLV:02:RES_REQ')
# Tubes
Valve1_Tube = Tube(color = 'black')
Valve2_Tube = Tube(color = 'red')

# unique id for the test based on date and time at which test was initiated
unique_id = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
logger.info("---------------------------------")
logger.info("---------------------------------")
logger.info("---------------------------------")
logger.info("TEST INITIATED at: %s" %unique_id)

#ask user input for which pump to use
while True:
	try:
		which_pump = int(input("which pump do you want to use?\n press:\t 1 -> LC-10Ai; 2 -> LC-20AT; 3 -> LC-20AD; 4 -> LC-20AP: ") )
	except ValueError:
		print ("sorry, I didn't understand that")
		continue
	if not which_pump in range (1,5):
		print("sorry, enter one of possible inputs")
		continue
	else:
		break  
pumps_dict = {1:'LC-10Ai', 2:'LC-20AT', 3:'LC-20AD', 4:'LC-20AP'}
this_pump = pumps_dict[which_pump]
# flow rate range for pumps
flow_range_dict = {'LC-10Ai':[0.001, 9.999] , 'LC-20AT': [0.001, 10.0], 'LC-20AD': [0.0001, 10.0], 'LC-20AP':[0.01, 150.0]}
Pump.min_flow = flow_range_dict[this_pump][0]
Pump.max_flow = flow_range_dict[this_pump][1]

# #ask user input for which selector box version is being used
# while True:
#     try:
#         sel_box_version = float(input("which selector box are you using?\n Mark [2/2.5/3]"))
#     except ValueError:
#         print ("sorry, I didn't understand that")
#         continue
#     if not sel_box_version in [2, 2.5, 3]:
#         print("sorry, enter one of possible inputs, just the numbers")
#         continue
#     else:
#         break

# get inner diameter of tube connected to valve 1 from user
while True:
	try:
		valve1_tube_inner_diameter = float(get_user_input("what is inner diameter (in um) of tube in valve 1? ", 30, "500"))
		break
	except ValueError:
		print("I couldnot understand your input")
		continue
# get inner diameter of tube connected to valve 2 from user
while True:
	try:
		valve2_tube_inner_diameter = float(get_user_input("what is inner diameter (in um) of tube in valve 2? ", 30, "127"))
		break
	except ValueError:
		print("I couldnot understand your input")
		continue
# get length of tube from user
# it is stored below as string
length_of_tube = get_user_input("what is length (with units) of pump being used?\nPress enter to proceed if you don't know the value ", 30, " ")
# record if inline filter has been changed
while True:
	inline_filter_change_status = get_user_input("Was the inline filter changed? ", 30, " ").lower()
	if not inline_filter_change_status in ['y', 'n', 'yes', 'no']:
		print("Please enter 'y' or 'n'")
		continue
	else:
		break

Valve1_Tube.inner_diameter = valve1_tube_inner_diameter
Valve2_Tube.inner_diameter = valve2_tube_inner_diameter
Valve1_Tube.length = valve1_tube_inner_diameter
Valve2_Tube.length = valve2_tube_inner_diameter


####################################### HPLC pump PULSATION TEST ###############################################
flow_rate = (Pump.min_flow + Pump.max_flow) / 2
logger.info("RUNNING HPLC PUMP PULSATION TEST")
# selecting the port for pulsation test
Actuator1.goto_port(5)
while True:
	pulsation = Pump.get_pulsation(flow_rate)
	logger.info("pulsation is %f" %pulsation)
	if get_user_confirmation("satisfied with pulsation test? [y/n]\n\tpress y if you want to continue\n\tpress n if you want to rerun the test: ", 30, 'y') == True:
		break
	else:
		input("did you repair the device? press enter key when ready")
		logger.info("re-running the pulsation test...")
		continue
logger.info("PULSATION TEST COMPLETE")


######################################### STANDATD LEAK TEST ####################################################
logger.info("LEAK TEST")
input("plug all water and sample valve ports. press  enter when done.")
# set max pressure to 500 more than upper pressure limit
while True:
	try:
		upper_pressure_limit = float(get_user_input("what is the upper pressure limit (psi) > ", 30, '3500'))
		break
	except ValueError:
		print("This is not a valid number")
		continue
Pump.max_pressure = upper_pressure_limit

# how many flow rates to test for each port
while True:
	try:
		how_many_flow_rates = int(get_user_input("how many flow rates do you want to test? ", 30, '10'))
		break
	except ValueError:
		print("This is not a valid number")
		continue
flow_rate_list = [Pump.min_flow + x*(Pump.max_flow-Pump.min_flow)/(how_many_flow_rates-1) for x in range(how_many_flow_rates-1)]
flow_rate_list.append(Pump.max_flow)

# leak test for a port
def leak_test(actuator_object, valve_number, port, flow_rate_list):
	# read the values for different time
	leak_test_dict = {}
	read_pressure = []
	read_flow_rate = []
	for flow_rate in flow_rate_list:
		logger.info("flow rate = %f ml/min" %flow_rate)
		# enable the flow with this flow rate on this port
		Pump.flow_rate = flow_rate
		Pump.start_pump(1)
		time.sleep(10)
		if Pump.status() == 65535:
			# this is case for pump error
			logger.error("error raised by the pump")
			leak_status = 0 # no leak
			logger.info("wait 30 second to clear error")
			time.sleep(30) # takes about 30 second to clear error
			Pump.clear_error()
			time.sleep(30)
			break
		else:
			try:
				pressure_settle_at = settled_value(read_pressure)
				leak_status = 1 #leak
			except StopIteration:
				leak_status = 0 #no leak

		read_pressure.append(Pump.pressure)
		# read_flow_rate.append(Pump.flow_rate)
		read_flow_rate.append(flow_rate)
		Pump.start_pump(0)
	leak_test_dict['flow_rate:valve%d:port%d'%(valve_number, port)] = read_flow_rate
	leak_test_dict['pressure:valve%d:port%d'%(valve_number, port)] = read_pressure
	return leak_test_dict, leak_status

def plot_leak_test(valve, leak_test_ports, leak_test_df):
	for index, port in enumerate(leak_test_ports):
		plt.subplot(1, 12, port)
		plt.plot(leak_test_df['flow_rate:valve%d:port%d'%(valve, port)], leak_test_df['pressure:valve%d:port%d'%(valve, port)])
		plt.title('port %d' %port)
		plt.xlabel('flow_rate (mL/min)')
		plt.ylabel('pressure (psi)')
	plt.tight_layout()
	plt.suptitle('pressure vs flow rate for valve %d' %valve)
	plt.subplots_adjust(top = 0.85)
	plt.savefig("./plots/leak_test/%s_pressure_vs_flow_rate:valve%d" %(unique_id, valve))


def leak_test_multiple_ports(actuator_object, valve_number, ports_to_test, flow_rate_list):
	leak_test_dict = {}
	leak_status_dict = {}
	for port in ports_to_test:
		actuator_object.goto_port(port)
		logger.info('actuator set to valve %d: port %d' %(valve_number, port))
		temp_dict, leakStatus = leak_test(actuator_object, valve_number, port, flow_rate_list)
		leak_test_dict.update(temp_dict)
		if leakStatus == 1:
			leak_status_dict['valve%d:port%d' %(valve_number, port)] = 'leaking'
		elif leakStatus == 0:
			leak_status_dict['valve%d:port%d' %(valve_number, port)] = 'not leaking'
		elif leakStatus == 2:
			leak_status_dict['valve%d:port%d' %(valve_number, port)] = 'not definitive'
	return leak_test_dict, leak_status_dict

# leak test for ports of both valves
logger.info("STARTING LEAK TEST")
leak_test_dict = {}
v1_leak_test_ports = list(range(1,13))
v2_leak_test_ports = list(range(1,13))

while True:
	run = 1
	leak_test_valve1_dict, leak_status_valve1_dict = leak_test_multiple_ports(Actuator1, 1, v1_leak_test_ports, flow_rate_list)
	leak_test_valve2_dict, leak_status_valve2_dict = leak_test_multiple_ports(Actuator2, 2, v2_leak_test_ports, flow_rate_list)
	leak_test_dict.update(leak_test_valve1_dict)
	leak_test_dict.update(leak_test_valve2_dict)
	leak_test_df = pd.DataFrame.from_dict(leak_test_dict, orient='index').transpose()
	logger.info('saving csv file at ./data/leak_test/')
	leak_test_df.to_csv("./data/leak_test/%s_leak_test_run_%d.csv" %(unique_id, run))
	# plot
	logger.info('plotting flow rate vs pressure. you can see the graph at ./plots/leak_test')
	for valve in (1,2):
		plot_leak_test(valve, v1_leak_test_ports, leak_test_df)
		plot_leak_test(valve, v2_leak_test_ports, leak_test_df)
	# display leak status
	logger.info("Here is the leak status:\n%s\n%s" %(leak_status_valve1_dict, leak_status_valve2_dict))
	# give user option to repair an rerun the leak test if there is leak
	if 'leaking' in leak_status_valve1_dict.values() or leak_status_valve2_dict.values():
		if get_user_confirmation("Do you want to repair the leaking tubes to rerun the leaking test? ", 30, 'n') == True:
			run += 1
			input('Repair those ports and press enter to continue')
			try:
				v1_leak_test_ports = list(map(int, input('what ports from valve 1 do you want to test (type them separated by comma): ').replace(' ', '').split(',')))
			except ValueError:
				v1_leak_test_ports = []
			try:
				v2_leak_test_ports = list(map(int, input('what ports from valve 2 do you want to test (type them separated by comma): ').replace(' ', '').split(',')))
			except ValueError:
				v2_leak_test_ports = []
			continue
		else:
			break
	else:
		break

logger.info("LEAK TEST COMPLETE")

if get_user_confirmation('Do you want to continue to characterization test?(yes/no) ', 300, 'n') == False:
	raise SystemExit

############################################ CHARACTERIZATION RUN ################################################3
logger.info("CHARACTERIZATION RUN")
# user inputs
input("make sure there is at least 750 mL of water for test/characterization. Then press enter")
while True:
	# port selection
	if get_user_confirmation("do you want to test all ports, flow rate? you can say \'no/n\'' if you want to manually select port and flow rate range. ", 30, 'y'):
		ports_to_test = list(range(1,13))
	else:
		ports_to_test = list(map(int, input('what ports do you want to test (type them separated by comma): ').replace(' ', '').split(',')))
	#  number of flow rate to test
	while True:
		try:
			how_many_flow_rates = int(input("How many flow rates do you want to test for each port? "))
			break
		except ValueError:
			print ("sorry, I didn't understand that")
			continue
	# find if user wants to characterize one or both valves, defalut is only the sample valve
	while True:
		try:
			which_valve_to_test = int(get_user_input("Which valves do you want to characterize?\n\twater valve -> press 1\n\tsample valve -> press 2\nboth sample and water valve -> press 3", 30, '2'))
			if not which_valve_to_test in [1,2,3]:
				print("please enter valid number")
				continue
			else:
				break
		except ValueError:
			print("please enter valid number")
			continue
	# find how long user wants to spend on each point (seconds), default to 30 seconds
	while True:
		try:
			how_long_at_each_point = int(get_user_input("How long do you want to characterize each port?(seconds) ", 30, '30'))
			break
		except ValueError:
			print("please enter valid integer number")
			continue
	# allow user to view list of entered parameters and 
	# provide estimated time of completion
	logger.info("These are the parameters you provided\n\
		   Tubing inner diameter(Valve 1): %f\n\
		   Tubing inner diameter(Valve 2): %f\n\
		   Minimium flow rate (mL/min): %f\n\
		   Maximum flow rate (mL/min): %f\n\
		   Number of flow rates to test for each port: %d\n\
		   Time at each point: %d seconds"\
		   %(Valve1_Tube.inner_diameter, Valve2_Tube.inner_diameter, Pump.min_flow, Pump.max_flow, how_many_flow_rates, how_long_at_each_point))
	if which_valve_to_test == 1:
		logger.info("Estimated time to complete the characterization: ~%f minutes" %(len(ports_to_test)*how_many_flow_rates*how_long_at_each_point/60))
	if which_valve_to_test == 2:
		logger.info("Estimated time to complete the characterization: ~%f minutes" %(2*len(ports_to_test)*how_many_flow_rates*how_long_at_each_point/60))
	# if user not satisfied with estimated time of completion, can re-enter the parameters again
	if get_user_confirmation("Satisfied with these selections? ", 30, 'y') == True:
		break
	else:
		continue

# below, it excludes the upper value in list that it returns
flow_rate_list = [Pump.min_flow + x*(Pump.max_flow-Pump.min_flow)/(how_many_flow_rates-1) for x in range(how_many_flow_rates-1)]
flow_rate_list.append(Pump.max_flow)

def characterization_run(actuator_object, tube_object, valve_number, flow_rate_list):
	logger.info("Valve = %d" %valve_number)	
	pumping_settling_time_dict = {}
	pumping_settling_time_dict['flow_rates'] = flow_rate_list
	characterization_df = pd.DataFrame()
	for port in ports_to_test:
		logger.info("port = %d" %port)
		temp_list = [] # to store the settling time for each flow rate for a port
		actuator_object.goto_port(port)
		for index, flow_rate in enumerate(flow_rate_list):
			logger.info("flow rate = %f" %flow_rate)
			temp_df = pd.DataFrame()
			read_pressure = []
			read_volume_used = []
			read_pump_status = []
			time_points = []
			FlowMeter.reset_flow_integrator('RES:%d:IntgFlow' %port)
			time_track = 0
			Pump.flow_rate = flow_rate
			# unit is um^3/min
			Pump.start_pump(1)
			while True:
				it = time.time()
				if Pump.status() == 65535:
					# this is case for pump error
					logger.error("error raised by the pump")
					logger.info("wait 30 second to clear error")
					time.sleep(30) # takes about 30 second to clear error
					Pump.clear_error()
					time.sleep(30)
					break
				time_track += 1
				read_pressure.append(Pump.pressure)
				if valve_number == 1:
					read_volume_used.append(flow_rate * time_track/60) # unit is mL
				if valve_number == 2:
					read_volume_used.append(FlowMeter.get_volume_used('RES:%d:IntgFlow' %port)) # unit is uL
				ft = time.time()
				time.sleep(1-ft+it)
				if time_track >= how_long_at_each_point:
					Pump.start_pump(0)
					break
			# find pressure settling time
			try:
				temp_list.append(settling_time(read_pressure))
			except StopIteration:
				temp_list.append('NaN')
			
			temp_df['pressure(valve%d)(port%d)(flow_rate%d)' %(valve_number, port, index+1)] = read_pressure
			temp_df['volume(valve%d)(port%d)(flow_rate%d)' %(valve_number, port, index+1)] = read_volume_used
			characterization_df = pd.concat([characterization_df, temp_df], axis = 1)
		pumping_settling_time_dict['valve%d:port%d'%(valve_number, port)] = temp_list # this list contains pressure settling time for different flow rates in increasing order
	time_points = list(range(1, how_long_at_each_point + 1))
	characterization_df['time'] = pd.Series(time_points)
	pumping_settling_time_df = pd.DataFrame(pumping_settling_time_dict)
	return characterization_df, pumping_settling_time_df

logger.info("STARTING CHARACTERIZATION TEST")
if which_valve_to_test == 1:
	char_df, settling_time_df = characterization_run(Actuator1, Valve1_Tube, 1, flow_rate_list)
	char_df.to_csv("./data/characterization/%s_characterization:valve1.csv" %unique_id)
	settling_time_df.to_csv("./data/characterization/%s_characterization:pressure_settling_time:valve1.csv" %unique_id)
if which_valve_to_test == 2:
	char_df, settling_time_df = characterization_run(Actuator2, Valve2_Tube, 2, flow_rate_list)
	char_df.to_csv("./data/characterization/%s_characterization:valve2.csv" %unique_id)
	settling_time.to_csv("./data/characterization/%s_characterization:pressure_settling_time:valve2.csv" %unique_id)
if which_valve_to_test == 3:
	char1_df, settling_time1_df = characterization_run(Actuator1, Valve1_Tube, 1, flow_rate_list)
	char2_df, settling_time2_df = characterization_run(Actuator2,Valve2_Tube, 2, flow_rate_list)
	char_df = pd.concat([char1_df, char2_df], axis = 1)
	settling_time_df = pd.concat([settling_time1_df, settling_time2_df], axis = 1)
	char_df.to_csv("./data/characterization/%s_characterization:valve1and2.csv" %unique_id)
	settling_time_df.to_csv("./data/characterization/%s_characterization_pressure_settling_time:valve1and2.csv" %unique_id)
logger.info("CHARACTERIZATION RUN COMPLETE")

################################################# PLOT from characterization data #############################################

def plot_vol_vs_time(flow_rates, df, valve, ports, uid):
	for index, flow_rate in enumerate(flow_rates):
		for i, port in enumerate(ports):
			plt.subplot(1, len(ports), i+1)
			plt.plot(df['time'], df['volume(valve%d)(port%d)(flow_rate%d)' %(valve, port, index+1)].tolist())
			plt.xlabel('time (seconds)')
			plt.ylabel('volume used (mL)')
		plt.legend(['flow= %.4f mL/min' %flow_rate for flow_rate in flow_rates])
		plt.suptitle("valve %d" %valve, fontsize="x-large")
	plt.savefig("./plots/characterization/%s_volume_vs_time:valve_%d" %(uid, valve))

def plot_pressure_vs_time(flow_rates, df, valve, ports, uid):
	for index, flow_rate in enumerate(flow_rates):
		for i, port in enumerate(ports):
			plt.subplot(1, len(ports), i+1)
			plt.plot(df['time'], df['pressure(valve%d)(port%d)(flow_rate%d)' %(valve, port, index+1)].tolist())
			plt.xlabel('time (seconds)')
			plt.ylabel('pressure (psi)')
		plt.legend(['flow= %.4f mL/min' %flow_rate for flow_rate in flow_rates])
		plt.suptitle("valve %d" %valve, fontsize="x-large")
	plt.savefig("./plots/characterization/%s_pressure_vs_time:valve_%d" %(uid, valve))

def plot_pressure_vs_flow_rate(flow_rates, df, valve, ports, uid):
	for i, port in enumerate(ports):
		final_pressure = []
		for i_f, flow_rate in enumerate(flow_rates):
			final_pressure.append(df['pressure(valve%d)(port%d)(flow_rate%d)' %(valve, port, i_f+1)].tolist()[-1])
		plt.subplot(1, len(ports), i+1)
		plt.plot(flow_rates, final_pressure) # pressure is settled pressure
		plt.title('port %d' %port)
		plt.xlabel('flow rate (mL/min)')
		plt.ylabel('pressure (psi)')
	plt.tight_layout()
	plt.suptitle("pressure vs flowrate for valve %d" %valve, fontsize = 'x-large')
	plt.subplots_adjust(top = 0.85)
	plt.savefig("./plots/characterization/%s_pressure_vs_flow_rate:valve%d" %(uid, valve))

logger.info("plotting the data...")
# plot vol vs time
if which_valve_to_test == 1 or which_valve_to_test == 2:
	plot_vol_vs_time(flow_rate_list, char_df, which_valve_to_test, ports_to_test, unique_id)
elif which_valve_to_test == 3:
	for valve in range(1,3): # 1 and 2 valves
		plot_vol_vs_time(flow_rate_list, char_df, valve, ports_to_test, unique_id)

# plot pressure vs time
if which_valve_to_test == 1 or which_valve_to_test == 2:
	plot_pressure_vs_time(flow_rate_list, char_df, which_valve_to_test, ports_to_test, unique_id)
elif which_valve_to_test == 3:
	for valve in range(1,3): # 1 and 2 valves
	plot_pressure_vs_time(flow_rate_list, char_df, valve, ports_to_test, unique_id)
		

# plot pressure vs flow rate
if which_valve_to_test == 1 or which_valve_to_test == 2:
	plot_pressure_vs_flow_rate(flow_rate_list, char_df, which_valve_to_test, ports_to_test, unique_id)


if which_valve_to_test == 3:
	for valve in range(1,3):
		plot_pressure_vs_flow_rate(flow_rate_list, char_df, valve, ports_to_test, unique_id)

logger.info("visit ./plots/characterization to view the plots")

##################################################### Saving results to confluence ################################################################