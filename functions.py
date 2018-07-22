import sys, select
from sample_delivery_system import Actuator
from sample_delivery_system import Pump, Actuator

def get_user_confirmation(prompt, timeout, default):
	# ask for user confirmation "y", "n", "yes" or "no"
	# timeout is in seconds
	# if doesnot input, by default, user agrees to the prompt
	while True:
		answer = ""
		print (prompt)
		i, o, e = select.select( [sys.stdin], [], [], timeout )
		# import pdb; pdb.set_trace()
		if (i):
			answer = sys.stdin.readline().strip().lower()
			if not answer in ["y", "n", "yes", "no"]:
				print ("I didn't get your input. you can only input \"y\" or \"n\".")
				continue
			else:
				break
		else:
			answer = default # by default, user agrees to the prommpt
			break
	return  answer == "y"

def get_user_input(prompt, timeout, default):
	# get input from users
	# timeout is in seconds
	# if doesnot input, pass the default value as string
	while True:
		answer = ""
		print (prompt)
		i, o, e = select.select( [sys.stdin], [], [], timeout)
		if (i):
			answer = sys.stdin.readline().strip().lower()
			break
		else:
			answer = default
			break
	return  answer
	# returns user input as string

def leastDiffFinder(listInp):
  diffList = list()
  reqIndex = 0
  listLen = len(listInp) 
  if listLen > 2:
    minDiff = abs(listInp[1]-listInp[0])
  for i in range((listLen-1)):
    thisDiff = abs(listInp[i+1]-listInp[i])
    if thisDiff<=minDiff and thisDiff < 2:
      minDiff = thisDiff
      diffList.append(i)      
  return diffList

def settled_value(listInp):
  listDiff = leastDiffFinder(listInp)
  if len(listDiff)==0:
    raise StopIteration # value didn't settle
  return listInp[max(listDiff)]

def settling_time(listInp):
  listDiff = leastDiffFinder(listInp)
  if len(listDiff)==0:
    raise StopIteration # value didn't settle
  return max(listDiff)+1 # because time is index + 1

# leak test functions -------------------------------------------------------

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

# characterization function -------------------------------------------------
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

# plot from leak test data ----------------------------------------------------
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


# plot from characterization data ----------------------------------------------
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
