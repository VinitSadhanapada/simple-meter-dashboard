import datetime
import random
import elmeasure_LG6400 as LG6400
import elmeasure_LG5220 as LG5220
import elmeasure_LG5310 as LG5310
import elmeasure_EN8410 as EN8410
import elmeasure_iELR300 as ELR300

from macros import DEV_ELM_LG6400, DEV_ELM_LG5310, DEV_ELM_LG5220, DEV_ELM_EN8400, DEV_ELM_EN8100, DEV_ELM_EN8410, DEV_ELM_ELR300
from macros import PARAMETERS

"""
MeterDevice Module for Individual Meter Communication.

This module defines the MeterDevice class which handles communication with
individual electrical meters via Modbus RTU protocol or simulation mode.
Supports multiple meter models with configurable parameters.
"""

class MeterDevice:
    """
    Represents a single meter device (real or simulated).

    Supports both real hardware communication via Modbus RTU and simulation mode
    for testing and development. Each device can read multiple electrical parameters
    such as voltage, current, power, and harmonics.

    Args:
        name (str): Device name.
        model (str): Device model/type.
        parameters (list): List of parameter names.
        client: Modbus client instance (None for simulation).
        error_file: File object for error logging.
        simulation_mode (bool): True for simulation, False for real meter.

    Attributes:
        name (str): Device identifier.
        model (str): Device model type.
        parameters (List[str]): Parameters being monitored.
        readings_count (int): Total number of successful readings performed.
        last_reading_time (datetime): Timestamp of most recent successful reading.
        simulation_mode (bool): Current operating mode (simulation vs hardware).
    
    Example:
        >>> # Create a simulated device
        >>> device = MeterDevice(
        ...     name="Main Meter", 
        ...     model="LG6400", 
        ...     parameters=["Voltage", "Current", "Power"],
        ...     simulation_mode=True
        ... )
        >>> readings = device.read_data()
        >>> print(f"Voltage: {readings[1]}V")
        
    Methods:
        read_data(): Returns a list of parameter values (simulated or real).
    """
    def __init__(self, name, model, parameters, client=None, error_file=None, simulation_mode=True, device_address=1):
        """
        Initialize a new MeterDevice instance.
        
        Args:
            name (str): Device identifier
            model (str): Device model (e.g., "LG6400")
            parameters (List[str]): Parameter names to read
            client (ModbusClient, optional): Modbus client for hardware communication
            error_file (TextIO, optional): Error logging file handle
            simulation_mode (bool): Enable simulation mode
            device_address (int): Modbus device address (1-247)
        """
        self.name = name
        self.model = model
        self.parameters = parameters
        self.client = client
        self.error_file = error_file
        self.simulation_mode = simulation_mode
        self.device_address = device_address
        self.reg_values = [0] * len(parameters)

    # Instance variable to control failure mode
    failure_mode = None  # e.g., 'phase_loss', 'overcurrent', etc.

    def read_data(self):
        """
        Read current parameter values from the meter device.
        In simulation mode, generates realistic values with small random variations and relationships.
        Failure modes can be triggered via self.failure_mode.
        """
        if self.simulation_mode:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            values = [now]
            # Default normal values (no-fault range)
            v_r = random.uniform(210, 240)
            v_y = random.uniform(210, 240)
            v_b = random.uniform(210, 240)
            a_r = random.uniform(0, 63)
            a_y = random.uniform(0, 63)
            a_b = random.uniform(0, 63)
            pf_r = random.uniform(0.95, 1.0)
            pf_y = random.uniform(0.95, 1.0)
            pf_b = random.uniform(0.95, 1.0)
            freq = random.uniform(49.5, 50.5)
            # Failure modes
            mode = self.failure_mode
            if mode == 'phase_loss':
                v_r = 0; a_r = 0; pf_r = 0
                v_y = 0; a_y = 0; pf_y = 0
                v_b = 0; a_b = 0; pf_b = 0
            elif mode == 'overcurrent':
                a_r = random.uniform(21, 25.5)
            elif mode == 'bad_pf':
                pf_r = pf_y = pf_b = random.uniform(0.6, 0.65)
            elif mode == 'overvoltage':
                v_b = random.uniform(265, 267.5)
            elif mode == 'reverse_power':
                pf_r = pf_y = pf_b = -random.uniform(0.95, 1.0)
            elif mode == 'freq_drift':
                freq = random.choice([random.uniform(48.25, 48.75), random.uniform(51.75, 52.25)])
            # Calculate watts per phase
            w_r = v_r * a_r * pf_r
            w_y = v_y * a_y * pf_y
            w_b = v_b * a_b * pf_b
            w_total = w_r + w_y + w_b
            # Averages
            v_avg = (v_r + v_y + v_b) / 3
            a_avg = (a_r + a_y + a_b) / 3
            pf_avg = (pf_r + pf_y + pf_b) / 3
            # Harmonics (no-fault range)
            v_r_harmo = random.uniform(0, 5)
            v_y_harmo = random.uniform(0, 5)
            v_b_harmo = random.uniform(0, 5)
            a_r_harmo = random.uniform(0, 8)
            a_y_harmo = random.uniform(0, 8)
            a_b_harmo = random.uniform(0, 8)
            # Energy counters (simulate monotonic increase)
            wh_received = getattr(self, '_wh_received', random.uniform(1000, 2000)) + random.uniform(1, 5)
            self._wh_received = wh_received
            load_hours = getattr(self, '_load_hours', random.uniform(100, 200)) + random.uniform(0.01, 0.05)
            self._load_hours = load_hours
            on_hours = getattr(self, '_on_hours', random.uniform(100, 200)) + random.uniform(0.01, 0.05)
            self._on_hours = on_hours
            no_of_intr = random.randint(0, 2) if mode == 'phase_loss' else random.randint(0, 1)
            # Clamp Watts Total to no-fault range
            w_total = max(0, min(w_total, 10000))
            # Map to parameter order
            param_map = {
                'Watts Total': w_total,
                'Watts R Ph': w_r,
                'Watts Y Ph': w_y,
                'Watts B Ph': w_b,
                'PF Ave': pf_avg,
                'PF R Ph': pf_r,
                'PF Y Ph': pf_y,
                'PF B Ph': pf_b,
                'VLN average': v_avg,
                'V R Ph': v_r,
                'V Y Ph': v_y,
                'V B Ph': v_b,
                'A average': a_avg,
                'A R Ph': a_r,
                'A Y Ph': a_y,
                'A B Ph': a_b,
                'Frequency': freq,
                'Wh received': wh_received,
                'Load Hours Delivered': load_hours,
                'No of interruption': no_of_intr,
                'On Hours': on_hours,
                'V R Harmonics': v_r_harmo,
                'V Y Harmonics': v_y_harmo,
                'V B Harmonics': v_b_harmo,
                'A R Harmonics': a_r_harmo,
                'A Y Harmonics': a_y_harmo,
                'A B Harmonics': a_b_harmo,
            }
            for param in self.parameters[1:]:
                values.append(round(param_map.get(param, 0), 2))
            self.reg_values = values
        else:
            # Check if client connection exists
            if self.client is None:
                # No hardware connection available - return -1 for all values
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.reg_values = [now] + [-1] * (len(self.parameters) - 1)
                if self.error_file:
                    self.error_file.write(f"[{now}] No hardware client connection available for device {self.name}\n")
            else:
                # Actual meter reading logic based on model
                if self.model == "LG6400":
                    self.reg_values = LG6400.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "EN8400":
                    self.reg_values = LG6400.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "EN8100":
                    self.reg_values = LG6400.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "LG+5220":
                    self.reg_values = LG5220.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "LG+5310":
                    self.reg_values = LG5310.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "EN8410":
                    self.reg_values = EN8410.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "ELR300":
                    self.reg_values = ELR300.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                else:
                    self.reg_values = [0] * len(self.parameters)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.reg_values[0] = now
        return self.reg_values