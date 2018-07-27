The purpose of this test is to characterize each port of sample delivery system. But first, pump pulsation is measured and each tubes is tested for leak. All these steps are carried out automatically by the python script.

* HPLC Pump Pulsation Test
At the beginning of the test, the software measures and reports pulsation of pump, with the option to repair the device and rerun the test.

* Standard Leak Test
The software steps through the ports using the flow profile as is determined by the pump model, testing for leaks. With the ports plugged, if the pressure reaches stability before the pump reaches an over pressure error, the pump has a leak. 

* Characterization Run
The standard characterization method is to test each port for settling time, pressure drop and flow rate characteristics of each port

<h2>Running the test</h2>

1. connect to ```username@psnxserv.slac.stanford.edu```

2. Then ```psbuild-rhel<x>```

3. source the conda environment: ```source /reg/g/pcds/pyps/conda/pcds_conda```

4. navigate to SDS_tst which is at ```/reg/neh/home5/gaire01/SDS_tst```

5. run ```python test.py```

logs are saved on ```.../SDS_tst/SDS_tst.log```

data are saved as csv on ```.../SDS_tst/data```

<h3>Outcome</h3>:

The software gives pressure and flow settling time, records and displays flow rate vs pressure, pressure vs time and volume vs time at the end of test. The software is able to identify and clear pump alarm such as over pressure error.

Furthermore, all data are saved in a place that is easy for the SLAC technicians and the users of that specific selector box to be recalled at the beam line experiment.
