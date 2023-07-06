import sys
import time
import logging

import odrive
from odrive.enums import *

class ODriveFailure(Exception):
    pass

class ODriveInterfaceAPI(object):
    driver = None
    encoder_cpr = 20480
    transmission_ratio = 14/32
    axis = None
    connected = False
    calibrated = False
    
    traj_start = None
    traj_end = None
    traj_waipoints = []
    
    #default speed & accel
    speed = 3
    accel = 3
    
    speed_limit = 20
    accel_limit = 40
    
    def __init__(self, active_odrive = None):
        if active_odrive:
            self.driver = active_odrive
            self.axis = self.driver.axis
            self.encoder_cpr = self.driver.axis.encoder.config.cpr
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
        
        self.driver.config.dc_bus_overvoltage_trip_level = 33
        self.driver.config.dc_max_positive_current = 2
        self.driver.config.dc_max_negative_current = -2
        self.axis.config.motor.motor_type = MotorType.HIGH_CURRENT
        self.axis.config.motor.torque_constant = 0.05513333333333333
        self.axis.config.motor.pole_pairs = 7
        self.axis.config.motor.current_soft_max = 70
        self.axis.config.motor.current_hard_max = 90
        self.axis.config.motor.calibration_current = 10
        self.axis.config.motor.resistance_calib_max_voltage = 2
        self.axis.config.calibration_lockin.current = 10
        self.axis.controller.config.control_mode = ControlMode.POSITION_CONTROL
        self.axis.controller.config.input_mode = InputMode.TRAP_TRAJ
        self.axis.trap_traj.config.vel_limit = self.speed_limit
        self.axis.trap_traj.config.accel_limit = self.accel_limit
        self.axis.trap_traj.config.decel_limit = self.accel_limit
        self.axis.controller.config.vel_limit = self.speed_limit
        self.axis.controller.config.vel_limit_tolerance = 1
        self.axis.config.torque_soft_min = -0.7718666666666667
        self.axis.config.torque_soft_max = 0.7718666666666667
        self.driver.inc_encoder0.config.cpr = 20480
        self.driver.inc_encoder0.config.enabled = True
        self.driver.config.gpio7_mode = GpioMode.DIGITAL
        self.axis.commutation_mapper.config.use_index_gpio = True
        self.axis.commutation_mapper.config.index_gpio = 7
        self.axis.pos_vel_mapper.config.use_index_gpio = True
        self.axis.pos_vel_mapper.config.index_gpio = 7
        self.axis.pos_vel_mapper.config.index_offset = 0
        self.axis.pos_vel_mapper.config.index_offset_valid = True
        self.axis.config.load_encoder = EncoderId.INC_ENCODER0
        self.axis.config.commutation_encoder = EncoderId.INC_ENCODER0
        
        self.axis.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
        time.sleep(1)
        while self.axis.current_state != AXIS_STATE_IDLE:
            time.sleep(0.1)
        if self.axis.active_errors != 0:
            print("Error handling")
            print("Active_errors: ", self.axis.active_errors)
            print("Disarm reason: ", self.axis.disarm_reason)
            return False
        
        if self.axis.procedure_result == PROCEDURE_RESULT_NOT_CALIBRATED:
            return False
        
        self.calibrated = True
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
        
    
    def set_traj_start(self):
        if not self.driver:
            return False
        
        
        self.traj_start = self.axis.pos_vel_mapper.pos_rel
        return True;
    
    
    def set_traj_end(self):
        if not self.driver:
            return False
        
        self.traj_end = self.axis.pos_vel_mapper.pos_rel
        return True;
    
    
    def go_to_start(self):
        if self.go_to(target_pos = self.traj_start):
            return True
        else:
            return False
         
            
    def go_to_end(self):
        if self.go_to(target_pos = self.traj_end):
            return True
        else:
            return False
       
    
    def go_to(self, target_pos, speed = None, accel = None):
        if not self.driver:
            return False
         
        if not self.engaged():
            return False
         
        if not (self.traj_end):
            return False
        
        if not (self.traj_start):
            return False
        
        if not ( ((self.traj_start <= target_pos) & (target_pos <= self.traj_end)) | ((self.traj_start >= target_pos) & (target_pos >= self.traj_end)) ):         
            return False
        
        
        if not speed:
            speed = self.speed
            
        if not accel:
            accel = self.accel
        
        if speed < self.speed_limit:
            self.axis.trap_traj.config.vel_limit = speed
         
        if accel < self.accel_limit:
            self.axis.trap_traj.config.accel_limit = accel
            self.axis.trap_traj.config.decel_limit = accel
            
        self.axis.controller.input_pos = target_pos
        while(abs(self.axis.pos_vel_mapper.pos_rel-target_pos) > 0.2):
            current_speed = self.axis.pos_vel_mapper.vel
            time.sleep(0.1)            
         
        return True
    
    def get_pos(self):
        if not self.driver:
            return False
        
        return self.axis.pos_vel_mapper.pos_rel
    
    def set_speed(self, speed):
        if not self.driver:
            return False
        
        if self.speed_limit < speed:
            return False
        
        self.speed = speed
        self.axis.trap_traj.config.vel_limit = self.speed
        return True
        
        
    def set_accel(self, accel):
        if not self.driver:
            return False
        
        if self.accel_limit < accel:
            return False
        
        self.accel = accel
        self.axis.trap_traj.config.accel_limit = self.accel
        self.axis.trap_traj.config.decel_limit = self.accel
        return True
        
        
           
           
           