import datetime
import random
import time
import elmeasure_LG6400 as LG6400
import elmeasure_LG5220 as LG5220
import elmeasure_LG5310 as LG5310
import elmeasure_EN8410 as EN8410
import elmeasure_iELR300 as ELR300

# Import RTC manager for reliable time keeping
try:
    from rtc_manager import RTCManager
    RTC_AVAILABLE = True
except ImportError:
    RTC_AVAILABLE = False

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
    def __init__(self, name, model, parameters, client=None, error_file=None, simulation_mode=True, device_address=1, rtc_manager=None):
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
            rtc_manager (RTCManager, optional): RTC manager for reliable timestamps
        """
        self.name = name
        self.model = model
        self.parameters = parameters
        self.client = client
        self.error_file = error_file
        self.simulation_mode = simulation_mode
        self.device_address = device_address
        self.reg_values = [0] * len(parameters)
        
        # Setup RTC manager for reliable time keeping
        self.rtc_manager = rtc_manager
        if self.rtc_manager is None and RTC_AVAILABLE:
            try:
                self.rtc_manager = RTCManager()
                # Don't initialize here to avoid delays - let the main app do it
            except Exception:
                self.rtc_manager = None
    
    def get_reliable_timestamp(self):
        """
        Get a reliable timestamp using RTC if available.
        
        Returns:
            str: Timestamp in YYYY-MM-DD HH:MM:SS format
        """
        try:
            if self.rtc_manager:
                reliable_time = self.rtc_manager.get_reliable_time()
                return reliable_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Fallback to system time
                return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            # Ultimate fallback
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def read_with_retry(self, max_attempts=5, attempt_timeout=1.0):
        """
        Attempt to get a meter reading with multiple tries.
        
        Makes up to 5 separate reading attempts, each with a 1-second timeout.
        Returns the first reading that actually completes (not necessarily "valid").
        This approach handles cases where the meter doesn't respond at all on some attempts.
        
        Args:
            max_attempts (int): Maximum number of reading attempts (default: 5)
            attempt_timeout (float): Timeout for each individual attempt (default: 1.0s)
            
        Returns:
            list: First successful meter reading, or -1 values if all attempts fail
        """
        for attempt in range(1, max_attempts + 1):
            try:
                if self.error_file:
                    now = self.get_reliable_timestamp()
                    self.error_file.write(f"[{now}] Reading attempt {attempt}/{max_attempts} for {self.name}\n")
                
                # Temporarily adjust client timeout for this attempt
                original_timeout = None
                if self.client and hasattr(self.client, 'timeout'):
                    original_timeout = self.client.timeout
                    self.client.timeout = attempt_timeout
                
                # Call the appropriate meter reading function
                reading = None
                if self.model == "LG6400":
                    reading = LG6400.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "EN8400":
                    reading = LG6400.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "EN8100":
                    reading = LG6400.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "LG+5220":
                    reading = LG5220.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "LG+5310":
                    reading = LG5310.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "EN8410":
                    reading = EN8410.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                elif self.model == "ELR300":
                    reading = ELR300.ReadMeterData(self.client, self.device_address, self.parameters, self.error_file)
                else:
                    reading = [0] * len(self.parameters)
                
                # Restore original timeout
                if original_timeout is not None and self.client:
                    self.client.timeout = original_timeout
                
                # Check if we got a reading (not None and has data)
                if reading is not None and len(reading) >= len(self.parameters):
                    if self.error_file:
                        now = self.get_reliable_timestamp()
                        self.error_file.write(f"[{now}] Successful reading obtained for {self.name} on attempt {attempt}\n")
                    return reading
                else:
                    if self.error_file:
                        now = self.get_reliable_timestamp()
                        self.error_file.write(f"[{now}] Attempt {attempt} returned no data or insufficient data for {self.name}\n")
                
            except Exception as e:
                # Restore original timeout if there was an exception
                if original_timeout is not None and self.client:
                    self.client.timeout = original_timeout
                    
                if self.error_file:
                    now = self.get_reliable_timestamp()
                    self.error_file.write(f"[{now}] Reading attempt {attempt} failed for {self.name}: {str(e)}\n")
        
        # All attempts failed
        if self.error_file:
            now = self.get_reliable_timestamp()
            self.error_file.write(f"[{now}] All {max_attempts} reading attempts failed for {self.name} - returning error values\n")
        
        return [-1] * len(self.parameters)

    def read_data(self):
        """
        Read current parameter values from the meter device.
        
        Uses a retry strategy with up to 5 attempts, each with 1-second timeout.
        Returns the first reading that actually completes, reducing issues with
        meters that don't respond on every attempt.
        
        Returns:
            List: Parameter values in the same order as self.parameters.
                 - Element 0: ISO format timestamp string (YYYY-MM-DD HH:MM:SS)
                 - Elements 1+: Numerical readings as floats
                 
        Example:
            >>> readings = device.read_data()
            >>> timestamp = readings[0]      # "2025-01-21 14:30:25"
            >>> voltage = readings[1]        # 230.5
            >>> current = readings[2]        # 5.2
            
        Note:
            In simulation mode, generates realistic values with small random variations.
            In hardware mode, tries up to 5 times (1 second each) to get a reading.
        """
        if self.simulation_mode:
            now = self.get_reliable_timestamp()
            values = [now]
            for _ in range(1, len(self.parameters)):
                values.append(round(random.uniform(0, 500), 2))
            self.reg_values = values
        else:
            # Check if client connection exists
            if self.client is None:
                # No hardware connection available - return -1 for all values
                now = self.get_reliable_timestamp()
                self.reg_values = [now] + [-1] * (len(self.parameters) - 1)
                if self.error_file:
                    self.error_file.write(f"[{now}] No hardware client connection available for device {self.name}\n")
            else:
                # Use the new retry logic: 5 attempts, 1 second each
                readings = self.read_with_retry(max_attempts=5, attempt_timeout=1.0)
                
                # Ensure we have the right number of values
                if len(readings) != len(self.parameters):
                    readings = readings[:len(self.parameters)] if len(readings) > len(self.parameters) else readings + [-1] * (len(self.parameters) - len(readings))
                
                self.reg_values = readings
            
            # Always update timestamp to current reliable time
            now = self.get_reliable_timestamp()
            self.reg_values[0] = now
            
        return self.reg_values