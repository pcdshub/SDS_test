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

