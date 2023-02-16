#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""

"""
from __future__ import print_function
from time import sleep
from os import system
from sys import stdout

from uldaq import (get_daq_device_inventory,AInScanFlag, ScanStatus,
                   ScanOption, create_float_buffer, DaqDevice, InterfaceType,
                   AiInputMode, AInFlag)

from uldaq.ul_enums import Range
from scipy.interpolate import interp1d
from numpy import sign
import time
from datetime import datetime, timezone
import struct


class DataLog:
    
    def start_data_capture(self, numAnalogFields=0, rate=10):
        timestr = time.strftime("%Y%m%d_%H%M%S")
        testStr = "data/L4_"
        filename = testStr+timestr+".dat"
        self.data_file = open(filename, "wb")
        self.num_a_fields = numAnalogFields
        self.rate = rate
        self.writeHeader()
        
    def end_data_capture(self):
        self.data_file.close()

    def write(self, data):
        self.data_file.write(data)
        
    def writeHeader(self):
        import sys
        self.data_file.write(b'\xDE\xAD\xBE\xEF')
        self.data_file.write((self.num_a_fields).to_bytes(2, byteorder=sys.byteorder, signed=False))
        self.data_file.write((self.rate).to_bytes(2, byteorder=sys.byteorder, signed=False))
        self.data_file.write(b'\xDE\xAD\xBE\xEF')
        # self.data_file.close()
        # pass
    
def scale(data_in, rng):
    
    rng_out = [-32768, 32767]
    if rng == Range.BIP10VOLTS:
        rng_in = [-10, 10]
    elif rng == Range.BIP5VOLTS:
        rng_in = [-5, 5]
        
    if rng_in[0] <= data_in <= rng_in[1]:
        m = interp1d(rng_in, rng_out)
        data_out = int(m(data_in))
    else:
        data_out = rng_out[1]*sign(data_in)
    return int(data_out)


def plotData(data):
    import matplotlib.pyplot as plt
    idx = range(0, len(data))
    plt.plot(idx, data)
    plt.show()
    
# lsb = 1
def main():
    """L4 Test Data Collection."""
    daq_device = None

    range_index = 0
    interface_type = InterfaceType.ANY
    low_channel = 0
    high_channel = 2
    samples_per_channel = 10000
    rate = 2000
    scan_options = ScanOption.CONTINUOUS
    flags = AInScanFlag.DEFAULT
    
    
    print("\n(  )  (  __)/ _\  / ___)(_  _)\n"
            "/ (_/\ ) _)/    \ \___ \  )(  \n"
            "\____/(__) \_/\_/ (____/ (__)   ")
    
    # Get descriptors for all of the available DAQ devices.
    devices = get_daq_device_inventory(interface_type)
    number_of_devices = len(devices)
    if number_of_devices == 0:
        raise RuntimeError('Error: No DAQ devices found')

    print('Found', number_of_devices, 'DAQ device(s):')
    for i in range(number_of_devices):
        print('  [', i, '] ', devices[i].product_name, ' (',
                devices[i].unique_id, ')', sep='')

    if number_of_devices > 1:
        descriptor_index = input('\nPlease select a DAQ device, enter a number'
                                + ' between 0 and '
                                + str(number_of_devices - 1) + ': ')
        descriptor_index = int(descriptor_index)
        if descriptor_index not in range(number_of_devices):
            raise RuntimeError('Error: Invalid descriptor index')
    else:
        descriptor_index = 0

    # Create the DAQ device from the descriptor at the specified index.
    daq_device = DaqDevice(devices[descriptor_index])

    # Get the AiDevice object and verify that it is valid.
    ai_device = daq_device.get_ai_device()

    # Establish a connection to the DAQ device.
    descriptor = daq_device.get_descriptor()
    print('\nConnecting to', descriptor.dev_string, '- please wait...')
    # For Ethernet devices using a connection_code other than the default
    # value of zero, change the line below to enter the desired code.
    daq_device.connect(connection_code=0)

    ai_info = ai_device.get_info()
    has_pacer = ai_info.has_pacer()
    scan_options = ai_info.get_scan_options()
    supports_iepe = ai_info.supports_iepe()
    # The default input mode is SINGLE_ENDED.
    # input_mode = AiInputMode.DIFFERENTIAL
    input_mode = AiInputMode.SINGLE_ENDED
    # Get the number of channels and validate the high channel number.
    number_of_channels = ai_info.get_num_chans_by_mode(input_mode)
    if high_channel >= number_of_channels:
        high_channel = number_of_channels - 1
    channel_count = high_channel - low_channel + 1

    # Get a list of supported ranges and validate the range index.
    ranges = ai_info.get_ranges(input_mode)
    if range_index >= len(ranges):
        range_index = len(ranges) - 1
    
    # Allocate a buffer to receive the data.
    data = create_float_buffer(channel_count, samples_per_channel)
    
    print('\n', descriptor.dev_string, ' ready', sep='')
    print('    Channels: ', low_channel, '-', high_channel)
    print('    Input mode: ', input_mode.name)
    print('    Range: ', ranges[range_index].name)
    print('    Samples per channel: ', samples_per_channel)
    print('    Rate: ', rate, 'Hz')
    print('    Scan options:', display_scan_options(scan_options))
    try:
        input('\nHit ENTER to continue\n')
    except (NameError, SyntaxError):
        pass

    system('clear')
    dataLog = DataLog()
    dataLog.start_data_capture(channel_count, rate)
    # all_data = [0]
################################################################################################       
# Scan Mode
################################################################################################
    # try:
        # Start the acquisition.
    rate = ai_device.a_in_scan(low_channel, high_channel, input_mode,
                                ranges[range_index], samples_per_channel,
                                rate, scan_options, flags, data)
    index = 0
    lastIndex = index
    firstTime = True
    try:
        while True:
            # Get the status of the background operation
            status, transfer_status = ai_device.get_scan_status()

            reset_cursor()
            print('Please enter CTRL + C to terminate the process\n')
            # print('Active DAQ device: ', descriptor.dev_string, ' (',
            #         descriptor.unique_id, ')\n', sep='')
            
            # The total number of samples transferred since the scan started.
            print('currentTotalCount = ',
                    transfer_status.current_total_count)
            
            # The number of samples per channel transferred since the scan started.
            print('currentScanCount = ',
                    transfer_status.current_scan_count)
            
            
            print('actual scan rate = ', '{:.6f}'.format(rate), 'Hz\n')
            print('lastIndex = ', lastIndex)

            # The index into the data buffer immediately following the last sample transferred.
            index = transfer_status.current_index
            print('currentIndex = ', index)
            
            if firstTime:
                chunk_size = 0
            else:
                # ai_device.scan_wait(WaitType.WAIT_UNTIL_DONE , -1)
                if (lastIndex > index):
                    chunk_tail = data[lastIndex:]
                    chunk_tail_binary = struct.pack('{:d}f'.format(len(chunk_tail)), *chunk_tail)
                    dataLog.write(chunk_tail_binary) 
                    lastIndex = 0
                chunk_size = index - lastIndex

            if chunk_size > 0:
                    
                print('chunk size: ', chunk_size, '\n')
                data_chunk = data[lastIndex:index]
                data_chunk_binary = struct.pack('{:d}f'.format(chunk_size), *data_chunk)
                dataLog.write(data_chunk_binary) 
                # if 'all_data' in locals():
                #     all_data += data_chunk
                # else:
                #     all_data = data_chunk
            else:
                pass
            
            if firstTime == False:
                lastIndex = index
                    
            # Display the data.
            # for i in range(channel_count):
            #     # clear_eol()
            #     print('chan =',
            #             i + low_channel, ': ','{:.6f}'.format(data[index + i]))
            firstTime = False
            sleep(.5)

    except KeyboardInterrupt:
        print('Stopped.')
        pass

    # except RuntimeError as error:
    #     print('\n', error)
    finally:
        dataLog.end_data_capture()
        if daq_device:
            # Stop the acquisition if it is still running.
            if status == ScanStatus.RUNNING:
                ai_device.scan_stop()
            if daq_device.is_connected():
                daq_device.disconnect()
            daq_device.release()
    # plotData(all_data)
    
    
def display_scan_options(bit_mask):
    """Create a displays string for all scan options."""
    options = []
    if bit_mask == ScanOption.DEFAULTIO:
        options.append(ScanOption.DEFAULTIO.name)
    for option in ScanOption:
        if option & bit_mask:
            options.append(option.name)
    return ', '.join(options)

def reset_cursor():
    """Reset the cursor in the terminal window."""
    stdout.write('\033[1;1H')

def clear_eol():
    """Clear all characters to the end of the line."""
    stdout.write('\x1b[2K')
    
if __name__ == '__main__':
    main()

