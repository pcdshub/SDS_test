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

# creat data directory if it already doesnot exists
data_dir = os.path.abspath('.') + '/data' 
if not os.path.exists(data_dir):
	os.makedirs(data_dir)

# ask user for prefix / macros.
prefix_sel_box = input('enter the prefix that is being used for selector box (eg: TST:SDS:SEL2:)')
prefix_pump = input('enter the prefix that is being used for the pump (eg: TST:LC20:SDS:)')

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
unique_id = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")
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
while True:
    try:
        sel_box_version = float(input("which selector box are you using?\n Mark [2/2.5/3]"))
    except ValueError:
        print ("sorry, I didn't understand that")
        continue
    if not sel_box_version in [2, 2.5, 3]:
        print("sorry, enter one of possible inputs, just the numbers")
        continue
    else:
        break

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

# leak test for ports of both valves
logger.info("STARTING LEAK TEST")
leak_test_dict = {}
v1_leak_test_ports = list(range(1,13))
v2_leak_test_ports = list(range(1,13))

while True:
	run = 1
	leak_test_valve1_dict, leak_status_valve1_dict = leak_test_multiple_ports(Pump, Actuator1, 1, v1_leak_test_ports, flow_rate_list)
	leak_test_valve2_dict, leak_status_valve2_dict = leak_test_multiple_ports(Pump, Actuator2, 2, v2_leak_test_ports, flow_rate_list)
	leak_test_dict.update(leak_test_valve1_dict)
	leak_test_dict.update(leak_test_valve2_dict)
	leak_test_df = pd.DataFrame.from_dict(leak_test_dict, orient='index').transpose()
	logger.info('saving csv file at ./data/leak_test/')
	leak_test_df.to_csv("./data/leak_test/%s_leak_test_run_%d.csv" %(unique_id, run))
	# plot
	logger.info('plotting flow rate vs pressure. you can see the graph at ./plots/leak_test')
	for valve in (1,2):
		plot_leak_test(valve, v1_leak_test_ports, leak_test_df, unique_id)
		plot_leak_test(valve, v2_leak_test_ports, leak_test_df, unique_id)
	# display leak status
	logger.info("Here is the leak status:\n%s\n%s" %(leak_status_valve1_dict, leak_status_valve2_dict))
	# give user option to repair an rerun the leak test if there is leak
	if ('leaking' in leak_status_valve1_dict.values()) or ('leaking' in leak_status_valve2_dict.values()):
		if get_user_confirmation("Do you want to repair the leaking tubes to rerun the leaking test?[y/n] ", 30, 'n') == True:
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

if get_user_confirmation('Do you want to continue to characterization test?[y/n] ', 300, 'n') == False:
	raise SystemExit

############################################ CHARACTERIZATION RUN ################################################3
logger.info("CHARACTERIZATION RUN")
# user inputs
input("make sure there is at least 750 mL of water for test/characterization. Then press enter")
while True:
	# port selection
	if get_user_confirmation("do you want to test all ports, flow rate?[y/n] you can say \'n\'' if you want to manually select port and flow rate range. ", 30, 'y'):
		ports_to_test = list(range(1,13))
	else:
		ports_to_test = list(map(int, input('what ports do you want to test (type them separated by comma): ').replace(' ', '').split(',')))
	#  number of flow rate to test
	while True:
		try:
			how_many_flow_rates = int(input("How many flow rates do you want to test for each port? "))
			break
		except ValueError:
			logger.error ("sorry, I didn't understand that. input integer value")
			continue
	
	if get_user_confirmation("do you want to characterize over the entire flow range of the pump?[y/n] ", 30, 'y') == True:
		flow_rate_list = [Pump.min_flow + x*(Pump.max_flow-Pump.min_flow)/(how_many_flow_rates-1) for x in range(how_many_flow_rates-1)]
		flow_rate_list.append(Pump.max_flow)
	else:
		print("flow range capacity of pump is: %s" %flow_range_dict[this_pump])
		while True:
			try:
				low_fr = float(input("what's the lowest flow rate to use? (mL/min) "))
				if low_fr < Pump.min_flow:
					low_fr = Pump.min_flow
				assert low_fr < Pump.max_flow
				break
			except ValueError:
				logger.error ("sorry, I didn't understand that. input float value")
				continue
			except AssertionError:
				logger.error ("min flow rate cannot be greater than max value of the pump")
				continue
		while True:
			try:
				high_fr = float(input("what's the high flow rate to use? (mL/min) "))
				if high_fr > Pump.max_flow:
					high_fr = Pump.max_flow
					assert high_fr > Pump.min_flow
				break
			except ValueError:
				logger.error ("sorry, I didn't understand that. input float value")
				continue
			except AssertionError:
				logger.error ("max flow rate cannot be greater than min value of the pump")
				continue
		flow_rate_list = [low_fr + x*(high_fr-low_fr)/(how_many_flow_rates-1) for x in range(how_many_flow_rates-1)]
		flow_rate_list.append(high_fr)
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
		   Ports to test: %s\n\
		   Number of flow rates to test for each port: %d\n\
		   Time at each point: %d seconds"\
		   %(Valve1_Tube.inner_diameter, Valve2_Tube.inner_diameter, Pump.min_flow, Pump.max_flow, ports_to_test, how_many_flow_rates, how_long_at_each_point))
	if which_valve_to_test == 1:
		logger.info("Estimated time to complete the characterization: ~%f minutes" %(len(ports_to_test)*how_many_flow_rates*how_long_at_each_point/60))
	if which_valve_to_test == 2:
		logger.info("Estimated time to complete the characterization: ~%f minutes" %(2*len(ports_to_test)*how_many_flow_rates*how_long_at_each_point/60))
	# if user not satisfied with estimated time of completion, can re-enter the parameters again
	if get_user_confirmation("Satisfied with these selections? [y/n] ", 30, 'y') == True:
		break
	else:
		continue



logger.info("STARTING CHARACTERIZATION TEST")
if which_valve_to_test == 1:
	char_df, settling_time_df = characterization_run(Pump, Actuator1, Valve1_Tube, 1, flow_rate_list, ports_to_test, how_long_at_each_point)
	char_df.to_csv("./data/characterization/%s_characterization:valve1.csv" %unique_id)
	settling_time_df.to_csv("./data/characterization/%s_characterization:pressure_settling_time:valve1.csv" %unique_id)
if which_valve_to_test == 2:
	char_df, settling_time_df = characterization_run(Pump, Actuator2, Valve2_Tube, 2, flow_rate_list, ports_to_test, how_long_at_each_point)
	char_df.to_csv("./data/characterization/%s_characterization:valve2.csv" %unique_id)
	settling_time.to_csv("./data/characterization/%s_characterization:pressure_settling_time:valve2.csv" %unique_id)
if which_valve_to_test == 3:
	char1_df, settling_time1_df = characterization_run(Pump, Actuator1, Valve1_Tube, 1, flow_rate_list, ports_to_test, how_long_at_each_point)
	char2_df, settling_time2_df = characterization_run(Pump, Actuator2,Valve2_Tube, 2, flow_rate_list, ports_to_test, how_long_at_each_point)
	char_df = pd.concat([char1_df, char2_df], axis = 1)
	settling_time_df = pd.concat([settling_time1_df, settling_time2_df], axis = 1)
	char_df.to_csv("./data/characterization/%s_characterization:valve1and2.csv" %unique_id)
	settling_time_df.to_csv("./data/characterization/%s_characterization_pressure_settling_time:valve1and2.csv" %unique_id)
logger.info("CHARACTERIZATION RUN COMPLETE")

################################################# PLOT from characterization data #############################################


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

# save device  and test information to a text file
ti = open("test_info.txt", "w+")
ti.write("unique id: %s\n" %unique_id)
ti.write("Pump type: %s\n" %pumps_dict[which_pump])
ti.write("Selector box version: %.1f\n" %sel_box_version)
ti.write("valve 1 tube inner diameter: %.4f um\n" %valve1_tube_inner_diameter)
ti.write("valve 2 tube inner diameter: %.4f um\n" %valve2_tube_inner_diameter)
ti.write("Was inline filter changed? %s\n" %inline_filter_change_status)
ti.write("pump pulsation: %.4f percent\n\n" %pulsation)
ti.write("LEAK TEST INFO\n")
ti.write("upper pressure limit: %.4f psi\n\n" %upper_pressure_limit)
ti.write("CHARACTERIZATION RUN INFO\n")
ti.write("Ports tested: %s\n" %ports_to_test)
ti.write("Flow rates tested: %s ml/min\n" %flow_rate_list)
ti.write("Time spent on each point: %d seconds\n" %how_long_at_each_point)
if which_valve_to_test == 1:
	ti.write("Valve tested: Water\n")
elif which_valve_to_test == 2:
	ti.write("Valve tested: Sample\n")
elif which_valve_to_test == 3:
	ti.write("Valve tested: Water, Sample\n")
ti.close()

images_to_attach = []

if get_user_confirmation("Do you want to save the data to confluence?[y/n]  ", 30000, 'y') == True:
	# device info
	contents = open("test_info.txt", "r")
	with open("test_info.html", "w+") as e:
		for lines in contents.readlines():
			e.write(lines.replace("\n","")+"<br />\n")
		# leak test image
		e.write("<h2>LEAK TEST PLOTS</h2><br />\n")
		e.write('<p><ac:image><ri:attachment ri:filename="leakv1_pressure_vs_flow_rate.png"/></ac:image></p>')
		images_to_attach.append("leakv1_pressure_vs_flow_rate.png")
		e.write('<p><ac:image><ri:attachment ri:filename="leakv2_pressure_vs_flow_rate.png"/></ac:image></p>')
		images_to_attach.append("leakv2_pressure_vs_flow_rate.png")
		
		# characterization run image
		e.write("<h2>CHARACTERIZATION</h2><br />\n")
		if which_valve_to_test == 1:
			e.write('<p><ac:image><ri:attachment ri:filename="charv1_pressure_vs_time.png"/></ac:image></p>')
			images_to_attach.append("charv1_pressure_vs_time.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv1_volume_vs_time.png"/></ac:image></p>')
			images_to_attach.append("charv1_volume_vs_time.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv1_pressure_vs_flow_rate.png"/></ac:image></p>')
			images_to_attach.append("charv1_pressure_vs_flow_rate.png")

		elif which_valve_to_test == 2:
			e.write('<p><ac:image><ri:attachment ri:filename="charv2_pressure_vs_time.png"/></ac:image></p>')
			images_to_attach.append("charv2_pressure_vs_time.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv2_volume_vs_time.png"/></ac:image></p>')
			images_to_attach.append("charv2_volume_vs_time.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv2_pressure_vs_flow_rate.png"/></ac:image></p>')
			images_to_attach.append("charv2_pressure_vs_flow_rate.png")
		elif which_valve_to_test == 3:
			e.write('<p><ac:image><ri:attachment ri:filename="charv1_pressure_vs_time.png"/></ac:image></p>')
			images_to_attach.append("charv1_pressure_vs_time.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv1_volume_vs_time.png"/></ac:image></p>')
			images_to_attach.append("charv1_volume_vs_time.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv1_pressure_vs_flow_rate.png"/></ac:image></p>')
			images_to_attach.append("charv1_pressure_vs_flow_rate.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv2_pressure_vs_time.png"/></ac:image></p>')
			images_to_attach.append("charv2_pressure_vs_time.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv2_volume_vs_time.png"/></ac:image></p>')
			images_to_attach.append("charv2_volume_vs_time.png")
			e.write('<p><ac:image><ri:attachment ri:filename="charv2_pressure_vs_flow_rate.png"/></ac:image></p>')
			images_to_attach.append("charv2_pressure_vs_flow_rate.png")

html_file = open('test_info.html', 'r')
html_string = html_file.read().strip().replace("\n","")
html_file.close()

from confluence import post_to_confluence
post_to_confluence("PCDS", "sample delivery system testing", unique_id, html_string, images_to_attach)
