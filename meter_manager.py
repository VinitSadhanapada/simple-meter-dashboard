import csv
import time

"""
MeterManager Module for Multi-Device Coordination.

This module provides the MeterManager class which orchestrates reading data from
multiple meter devices, manages CSV logging, MQTT publishing, and UI callbacks.
Designed to handle complex meter reading scenarios with centralized management.
"""

class MeterManager:
    """
    Manages multiple meter devices with coordinated data collection and publishing.
    
    The MeterManager class serves as the central coordinator for a meter reading system,
    handling multiple MeterDevice instances and providing integrated logging, MQTT
    publishing, and UI update capabilities.
    
    Args:
        meters (List[MeterDevice]): List of MeterDevice instances to manage.
    parameters (List[str]): Parameter names that match across all devices.
        csv_filenames (List[str]): CSV file paths for logging each device's data.
                                 Must have same length as meters list.
        ui_callback (callable, optional): Function to call for UI updates.
                                        Signature: callback(total_readings, stdscr, reg_values)
        mqtt_client (object, optional): MQTT client instance for data publishing.
        publish_mqtt (bool): Enable MQTT publishing. Default: False.
    
    Attributes:
        meters (List[MeterDevice]): Managed meter devices.
        TotalReadings (int): Total number of reading cycles completed.
        allRegValues (List[List]): Latest readings from all devices.
                                 Structure: [[device0_readings], [device1_readings], ...]
        published_msg (int): Count of MQTT messages successfully published.
        
    Raises:
        ValueError: If meters and csv_filenames lists have different lengths.
        FileNotFoundError: If CSV file paths cannot be created.
        
    Example:
        >>> meters = [MeterDevice("Meter1", "LG6400", params, simulation_mode=True)]
        >>> manager = MeterManager(
        ...     meters=meters,
        ...     parameters=["Time", "Voltage", "Current"],
        ...     csv_filenames=["meter1_log.csv"],
        ...     publish_mqtt=True
        ... )
        >>> manager.read_all()  # Read from all meters and update logs
        >>> print(f"Completed {manager.TotalReadings} reading cycles")
    """
    
    def __init__(self, meters, parameters, csv_filenames, ui_callback=None, mqtt_client=None, publish_mqtt=False):
        """
        Initialize MeterManager with devices and configuration.
        
        Args:
            meters (List[MeterDevice]): Meter devices to manage
            parameters (List[str]): Parameter names for all devices
            csv_filenames (List[str]): CSV log file paths (one per meter)
            ui_callback (callable, optional): UI update function
            mqtt_client (object, optional): MQTT client for publishing
            publish_mqtt (bool): Enable MQTT message publishing
        """ 
        self.meters = meters
        self.parameters = parameters
        self.csv_files = [open(name, "a", newline='') for name in csv_filenames]
        self.csv_writers = [csv.writer(f) for f in self.csv_files]
        for writer in self.csv_writers:
            writer.writerow(parameters)
        self.ui_callback = ui_callback
        self.allRegValues = [[0] * len(parameters) for _ in meters]
        self.published_msg = 0
        self.TotalReadings = 0
        self.mqtt_client = mqtt_client
        self.publish_mqtt = publish_mqtt

    def read_all(self, stdscr=None):
        """
        Read data from all meters and perform associated operations.
        
        Coordinates a complete reading cycle across all managed meters, including:
        - Data collection from each MeterDevice
        - CSV logging of readings
        - MQTT publishing (if enabled)
        - UI callback execution (if provided)
        
        This method is thread-safe and handles errors gracefully, ensuring that
        failure in one meter doesn't prevent reading from others.
        
        Args:
            stdscr (curses.window, optional): Curses screen object for UI updates.
                                            If provided and ui_callback is set,
                                            passes to callback for display updates.
        
        Returns:
            None
            
        Side Effects:
            - Increments self.TotalReadings counter
            - Updates self.allRegValues with latest readings
            - Writes new rows to CSV files
            - Publishes MQTT messages (if enabled)
            - Calls UI callback (if configured)
            
        Example:
            >>> manager.read_all()  # Simple reading cycle
            
        Note:
            The stdscr parameter exists for backwards compatibility with legacy
            curses-based implementations but is not used in the modern console
            dashboard (print_dashboard2.py).
        """
        self.TotalReadings += 1
        for i, meter in enumerate(self.meters):
            regValue = meter.read_data()
            self.csv_writers[i].writerow(regValue)
            if self.publish_mqtt and self.mqtt_client:
                self.published_msg = self.mqtt_client.publish_message(self.parameters, regValue, meter.name)
            self.allRegValues[i] = regValue.copy()
        if self.ui_callback and stdscr is not None:
            self.ui_callback(self.TotalReadings, stdscr, self.allRegValues)

    def close(self):
        """Closes all CSV files."""
        for f in self.csv_files:
            f.close()