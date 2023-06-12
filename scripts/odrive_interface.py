import sys
import time
import logging

import odrive
from odrive.enums import *

class ODriveFailure(Exception):
    pass

class ODriveInterfaceAPI(object):
    driver = None
    encoder_cpr = 4096
    axis = None
    connected = False
    calibrated = False
    
    def __init__(self, active_odrive = None):
        if active_odrive:
            self.driver = active_odrive
            self.axis = self.driver.axis0
            self.encoder_cpr = self.driver.axis0.encoder.config.cpr
            self.connected = True
            #self.calibrated = ...
            
    def __del__(self):
        self.disconnect()
        
    def connect(self, port = None, timeout = 5):
        if self.driver:
            print("already connected")
        try: 
            self.driver = odrive.find_any(timeout = timeout)
        except:
            print("no odrive found")
            return False
        
        self.axis = self.driver.axis0
        
        #check for errors!
        
        self.encoder_cpr = self.driver.inc_encoder0.config.cpr
        self.connected = True
        self.calibrated = False
        
        return True
    
    def disconnect(self):
        self.connected = False
        self.axis = None
        
        if not self.driver:
            print("not connected")
            return False
        
        try:
            self.release()
        except:
            return False
        finally:
            self.driver = None
        return True;
    
    def calibrate(self):
        if not self.driver:
            print("not connected")
            return False
        
        self.axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        time.sleep(1)
        while self.axis.current_state != AXIS_STATE_IDLE:
            time.sleep(0.1)
        if self.axis.active_errors != 0:
            print("handle errors here")
            return False
        
        return True
    
    def engaged(self):
        if self.driver and hasattr(self, 'axis'):
            return self.axis.current_state == AXIS_STATE_CLOSED_LOOP_CONTROL
        else:
            return False
    
    def idle(self):
        if self.driver and hasattr(self, 'axis'):
            return self.axis.current_state == AXIS_STATE_IDLE
        else:
            return False
        
    def engage(self):
        if not self.driver:
            return False
    
        #self.logger.debug("Setting drive mode.")
        self.axis.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
        
        #self.engaged = True
        return True
        
    def release(self):
        if not self.driver:
            return False
        
        #self.logger.debug("Releasing.")
        self.axis.requested_state = AXIS_STATE_IDLE
    
        #self.engaged = False
        return True
        