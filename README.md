# PyAMLController

This is a Python driver and widget for the Arun Microelectronics LTD- Model NGC3 pressure gauge controller.

This code has only ben tested on Windows 10, Python3 using an ion gauge all other gauges should function but have not been tested. If you test it on other operating systems, please let me know if it worked or not. The widget may not be very well written, improvements/suggestions are welcome.

# Requirements

## Driver only

Pandas  
PyVisa  
PyVisa-py  
Pandas  

## Widget

Matplotlib  
Seaborn  
PyQt5  

# Usage

To run the widget, run the aml_controller_app.py file. Most of the features are self explanatory. The only unusual features are that if Filename is left empty or is a directory, a 'tmp' file will be created in the CWD or in the indicated directory, respectively, and will be overwritten the first time Start/Save is clicked after opening or after "Clear" is clicked. All other Filenames will will have the date and time appened if the filename is already in use.


The driver is in the AML_NGC3.py file. The attributes are:

_remote (Boolean)  
_gauge_on (Boolean)    
_current (float 0.5 or 5)    
_filament (int 1 or 2)  

Example code:

        import pyvisa as visa
        from AML_NGC3 import NGC3
        
        rm = visa.ResourceManager('@py') 
        port = rm.list_resources()[0] # Choose the index that matched the COM port
        ig = NGC3(rm, port)
        
        
        ig.remote = False   # set to locate controls (on the controller front panel)
        if.remote           # returns True if set to remote control, False if set to local controls
        
        ig.filament = 1     # set to filament 1
        print("Using filament number {}".format(ig.filament)) # Gets and print the set filament number
        
        ig.current = 0.5    # set current to 0.5 or 5mA
        ig.current          # get current
        
        ig.gauge_on = False # Turn off the ion gauge
        ig.gauge_on         # returns True if the gauge is on, false if it's off
        
        print(ig.status()) # Print a list of tupplets. Each tupplet contains the gauge name, pressure (or temperature) and units
        
        
