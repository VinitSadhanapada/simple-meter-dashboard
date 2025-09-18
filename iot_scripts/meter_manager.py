import csv
import time
from datetime import datetime


def format_csv_value(value, param_name):
    """
    Format a value for CSV output with simple, consistent formatting.

    Args:
        value: The raw value from meter reading
        param_name: The parameter name to determine formatting

    Returns:
        str: Formatted value string
    """
    if value in [0, "0", "0.0", 0.0]:
        return "0"

    try:
        # Convert to float for formatting
        float_val = float(value)

        # Round to 2 decimal places for most values
        if float_val == int(float_val):
            return str(int(float_val))  # No decimals for whole numbers
        else:
            return f"{float_val:.2f}"  # 2 decimal places for others

    except (ValueError, TypeError):
        # If conversion fails, return as string
        return str(value)


def create_formatted_csv_header(parameters):
    """
    Create a simple, readable CSV header by cleaning up parameter names.

    Returns:
        list: Formatted header row
    """
    formatted_headers = ["Location", "Device_ID", "Meter_Name"]
    # Insert 'Time' and 'Model' in the correct order
    for i, param in enumerate(parameters):
        clean_name = param.replace(" ", "_").replace(
            ".", "").replace("(", "").replace(")", "")
        if i == 0:
            # After 'Time', insert 'Model'
            formatted_headers.append(clean_name)
            formatted_headers.append("Model")
        else:
            formatted_headers.append(clean_name)
    return formatted_headers


"""
MeterManager Module for Multi-Device Coordination.

This module provides the MeterManager class which orchestrates reading data from
multiple meter devices, manages CSV logging, MQTT publishing, and UI callbacks.
Designed to handle complex meter reading scenarios with centralized management.
"""


class MeterManager:
    def _ensure_csv_file(self):
        """
        Ensure the CSV file exists and is open for appending. If deleted, recreate and write header.
        """
        import os
        file_path = self.csv_file.name if hasattr(self, 'csv_file') else None
        need_header = False
        if file_path is not None:
            if self.csv_file.closed or not os.path.exists(file_path):
                try:
                    self.csv_file = open(file_path, "a", newline='')
                    self.csv_writer = csv.writer(self.csv_file)
                    # If file is empty, write header
                    self.csv_file.seek(0, 2)
                    if self.csv_file.tell() == 0:
                        need_header = True
                except Exception as e:
                    print(f"Error reopening CSV file {file_path}: {e}")
                    return
        if need_header:
            try:
                formatted_headers = create_formatted_csv_header(
                    self.parameters)
                self.csv_writer.writerow(formatted_headers)
                self.csv_file.flush()
            except Exception as e:
                print(f"Error writing header to CSV: {e}")

    def get_all_meter_readings(self):
        """
        Returns a list of dicts with device info and latest readings for all meters.
        Each dict contains: 'device_id', 'device_name', 'model', 'readings' (list of parameter values)
        """
        result = []
        for i, meter in enumerate(self.meters):
            info = {
                'device_id': getattr(meter, 'device_address', i+1),
                'device_name': getattr(meter, 'name', f"Meter_{i+1}"),
                'model': getattr(meter, 'model', 'Unknown'),
                'readings': self.allRegValues[i] if i < len(self.allRegValues) else []
            }
            result.append(info)
        return result
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
                                        Signature: callback(
                                            total_readings, stdscr, reg_values)
        mqtt_client (object, optional): MQTT client instance for data publishing.
        publish_mqtt (bool): Enable MQTT publishing. Default: False.

    Attributes:
        meters (List[MeterDevice]): Managed meter devices.
        TotalReadings (int): Total number of reading cycles completed.
        allRegValues (List[List]): Latest readings from all devices.
                                 Structure: [[device0_readings],
                                     [device1_readings], ...]
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

    def __init__(self, meters, parameters, csv_filenames, location=None, ui_callback=None, mqtt_client=None, publish_mqtt=False, enable_csv_write=True):
        self.location = location
        """
        Initialize MeterManager with devices and configuration.

        Args:
            meters (List[MeterDevice]): Meter devices to manage
            parameters (List[str]): Parameter names for all devices
            csv_filenames (List[str]): CSV log file paths (should be a single file per location)
            ui_callback (callable, optional): UI update function
            mqtt_client (object, optional): MQTT client for publishing
            publish_mqtt (bool): Enable MQTT message publishing
        """
        self.meters = meters
        self.parameters = parameters

        self.enable_csv_write = enable_csv_write
        if self.enable_csv_write:
            # Only one CSV file per location is supported
            if len(csv_filenames) != 1:
                raise ValueError(
                    "MeterManager expects a single CSV file per location (all meters in one file).")
            try:
                self.csv_file = open(csv_filenames[0], "a", newline='')
            except Exception as e:
                print(f"Error opening CSV file {csv_filenames[0]}: {e}")
                raise
            self.csv_writer = csv.writer(self.csv_file)
            # Write header if file is empty
            try:
                self.csv_file.seek(0, 2)  # Seek to end
                if self.csv_file.tell() == 0:
                    formatted_headers = create_formatted_csv_header(parameters)
                    self.csv_writer.writerow(formatted_headers)
                self.csv_file.seek(0, 2)
            except Exception as e:
                print(f"Error writing header to CSV: {e}")
        self.ui_callback = ui_callback
        self.allRegValues = [[0] * len(parameters) for _ in meters]
        self.published_msg = 0
        self.TotalReadings = 0
        self.mqtt_client = mqtt_client
        self.publish_mqtt = publish_mqtt

    def read_all(self, stdscr=None, inter_device_delay=0.1, reading_time=None):
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
            inter_device_delay (float): Delay in seconds between reading each device.
                                      Default: 0.1 seconds (100ms)

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
            # With 200ms delay between devices
            >>> manager.read_all(inter_device_delay=0.2)

        Note:
            The stdscr parameter exists for backwards compatibility with legacy
            curses-based implementations but is not used in the modern console
            dashboard (print_dashboard2.py).
        """
        self.TotalReadings += 1
        meter_data_list = []
        for i, meter in enumerate(self.meters):
            regValue = meter.read_data()
            if self.enable_csv_write:
                # Ensure CSV file exists and is open before writing
                self._ensure_csv_file()
                try:
                    formatted_row = [
                        self.location if self.location else "Unknown",
                        getattr(meter, 'device_address', i + 1),
                        getattr(meter, 'name', f"Meter_{i+1}")
                    ]
                    for j, value in enumerate(regValue):
                        if j == 0:  # Timestamp - keep as-is
                            formatted_row.append(value)
                            # Insert model after time
                            formatted_row.append(
                                getattr(meter, 'model', 'Unknown'))
                        else:
                            param_name = self.parameters[j] if j < len(
                                self.parameters) else "Unknown"
                            formatted_value = format_csv_value(value, param_name)
                            formatted_row.append(formatted_value)
                    self.csv_writer.writerow(formatted_row)
                    self.csv_file.flush()
                except Exception as e:
                    print(f"Error writing to CSV file: {e}")

            if self.publish_mqtt and self.mqtt_client:
                self.published_msg = self.mqtt_client.publish_message(
                    self.parameters, regValue, meter.name)
            self.allRegValues[i] = regValue.copy()

            # --- DB dict construction ---
            # Only use a valid ISO timestamp string; otherwise, use current time
            failed_read = not regValue or (isinstance(regValue, list) and all(
                (v == -1 or v is None) for v in regValue))
            ts = regValue[0] if regValue and len(regValue) > 0 else None
            if isinstance(ts, str) and ('T' in ts) and (len(ts) >= 16):
                meter_time = ts
            ts = regValue[0] if regValue and len(regValue) > 0 else None
            if reading_time is not None:
                meter_time = reading_time
            elif isinstance(ts, str) and ('T' in ts) and (len(ts) >= 16):
                meter_time = ts
            else:
                meter_time = datetime.now().isoformat()
                print(
                    f"DEBUG: meter_time to be used: {meter_time} (type: {type(meter_time)})")
            meter_data = {
                "Device_ID": getattr(meter, 'device_address', i + 1),
                "Meter_Name": getattr(meter, 'name', f"Meter_{i+1}"),
                "Time": meter_time,
                "Model": getattr(meter, 'model', 'Unknown'),
            }
            for j, param in enumerate(self.parameters):
                # Never overwrite 'Time' or 'Model' keys
                if param in ("Time", "Model"):
                    continue
                if failed_read:
                    meter_data[param] = None
                elif j < len(regValue):
                    meter_data[param] = regValue[j]
                else:
                    meter_data[param] = None
            print(
                f"DEBUG: meter_data constructed in MeterManager: {meter_data}")
            meter_data_list.append(meter_data)
        return meter_data_list
