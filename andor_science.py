######################################
###### ANDOR iXon Python Wrapper #####
######################################


#   pyAndor - A Python wrapper for Andor's scientific cameras
#   Copyright (C) 2009  Hamid Ohadi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


####################################################################
###### Modified and expanded on by Pierre, Nick, Sebastien and #####
###### Kevin at ObsPM&Subaru Telescope 2018/2020    	       #####
####################################################################

from ctypes import *
import time
from PIL import Image

__all__ = ['Andor']


# Camera serial numbers
CAMERA_SERIAL = {'Luca' : 317,
'Ixion' : 11378}

# To keep to count of how many times camera initialization have been tried
INSTANCE_NUMBER = 0

"""Andor class which is meant to provide the Python version of the same
   functions that are defined in the Andor's SDK. Since Python does not
   have pass by reference for immutable variables, some of these variables
   are actually stored in the class instance. For example the temperature,
   gain, gainRange, status etc. are stored in the class. """


class Andor(object):
    def __init__(self, camera_name=None):

        # To install these libraries, see in the andor SDK doc, at section 2 - software installation.
        # After running the code, if there is a 'Open() failed' error message, look in
        # the /usr/local/etc/andor/INSTALL.txt file at the 'Open() failed ERROR' section.
        cdll.LoadLibrary("/usr/local/lib/libandor.so".encode('ascii'))
        self.dll = CDLL("/usr/local/lib/libandor.so".encode('ascii'))
   
        # Manage the case of having several andor cameras installed in the same computer
        self.GetAvailableCameras()

        if self.total_cameras > 1:
            #for i in range(self.total_cameras):
            #    self.GetCameraHandle(i)
            #    print("Camera nbr %d has handle: %d" % (i, self.camera_handle))

            global INSTANCE_NUMBER
            self.GetCameraHandle(INSTANCE_NUMBER)
            INSTANCE_NUMBER += 1
            # (Luca) camera_handle = 100; cam_index = 0; serial = 317
            # (iXon Ultra EMCCD 897, science camera) camera_handle = 201; cam_index = 1; serial = 11378
            self.SetCurrentCamera(self.camera_handle)

        # Initialize the camera
        self.dll.Initialize("/usr/local/etc/andor".encode('ascii'))

        # Store the serial number of the camera
        self.GetCameraSerialNumber()


        # Initialize the attributes
        #cw                  = c_int()
        #ch                  = c_int()
        #self.dll.GetDetector(byref(cw), byref(ch))
        #self.width          = cw.value
        #self.height         = cw.value



        #self.temperature    = None
        #self.gain           = None
        #self.gainRange      = None
        #self.status         = None
        #self.pixsize        = None
        #self.numberframes   = 1
        #self.maxbuffersize  = None
        #self.max_exp        = 0.

    def __del__(self):
        print("Camera released.")

    #-------------------------------------------------------------------------
    #  General camera stuff 
    #-------------------------------------------------------------------------

    def GetAvailableCameras(self):
        '''
        This function gets the total number of Andor cameras currently installed.
        NOTE: it is possible to call this function before any of the cameras are initialized.
        '''
        c_total_cameras = c_long()
        error = self.dll.GetAvailableCameras(byref(c_total_cameras))
        self.total_cameras = c_total_cameras.value
        return ERROR_CODE[error]

    def GetHeadModel(self):
        '''
        This function will retrieve the type of CCD attached to the system.
        NOTE: works only after the camera is intialized.
        '''
        c_name = c_char()
        error = self.dll.GetHeadModel(byref(c_name))
        self.head_model = c_name.value
        return ERROR_CODE[error]

    def GetCameraHandle(self, camera_index):
        '''
        This function gets the handle for the camera specified by cameraIndex.
        NOTE: it is possible to call this function before any of the cameras are initialized.

        Parameters
        ----------
        camera_index : long
            Index of any of the installed cameras. From 0 to the total number of camera installed.
            The total number of camera installed can be retrieved with GetAvailableCameras method.
        '''
        c_camera_handle = c_long()
        error = self.dll.GetCameraHandle(camera_index, byref(c_camera_handle))
        self.camera_handle = c_camera_handle.value
        return ERROR_CODE[error]

    def SetCurrentCamera(self, camera_handle):
        '''
        When multiple Andor cameras are installed this function allows the user to select which
        camera is currently active.
        NOTE: it is possible to call this function before any of the cameras are initialized.

        Parameters
        ----------
        camera_handle : long
            Handle of the camera. Can be retrieved with GetCameraHandle method.
        '''
        error = self.dll.SetCurrentCamera(camera_handle)
        return ERROR_CODE[error]

    def GetCameraSerialNumber(self):
        '''
        This function will retrieve camera’s serial number.
        NOTE: works only after the camera is intialized.
        '''
        c_number = c_int()
        error = self.dll.GetCameraSerialNumber(byref(c_number))
        self.camera_serialnumber = c_number.value
        return ERROR_CODE[error]

    def GetCurrentCamera(self):
        """
        When multiple Andor cameras are installed, this function gets the handle of the currently
        initialized one.
        NOTE: works only after the camera is initialized.
        """
        c_current_handle = c_long()
        error = self.dll.GetCurrentCamera(byref(c_current_handle))
        self.current_handle = c_current_handle.value
        return ERROR_CODE[error]

    def GetStatus(self):
        status = c_int()
        error = self.dll.GetStatus(byref(status))
        self.Get_status_error = error
        self.status = ERROR_CODE[status.value]
        return ERROR_CODE[error]

    def ShutDown(self):
        # First wait for the temperature to raise up slowly
        # to avoid it rise faster than certified
        self.GetTemperature()
        if self.temperature < -20:
            self.CoolerOFF()
        while self.temperature < -20:
            time.sleep(2)
            self.GetTemperature()
            print("Current temperature is: " + str(self.temperature))

        error = self.dll.ShutDown()
        return ERROR_CODE[error]

    def FreeInternalMemory(self):
        """
        This function purges the internal memory of the iXon of any 
        previous data stored from the last acquisition.
        """
        error = self.dll.FreeInternalMemory()
        return ERROR_CODE[error]

    def SetSpool(self, active, method, path, framebuffersize):
        error = self.dll.SetSpool(c_int(active),
                                  c_int(method),
                                  byref(path),
                                  c_int(framebuffersize))
        return ERROR_CODE[error]

    def GetPixelSize(self, xSize=1, ySize=1):
        xSize = c_float()
        ySize = c_float()
        error = self.dll.GetPixelSize(byref(xSize), byref(ySize))
        self.pixsize = (xSize.value, ySize.value)
        return ERROR_CODE[error]

    #-------------------------------------------------------------------------
    #  Temperature 
    #-------------------------------------------------------------------------

    def CoolerON(self):
        """
        Switches ON the Cooling. On Some systems the temp change is controlled.
        The Temp to witch the detector will be cooled is set via "SetTemperature". The Hardware does the rest.
        """
        error = self.dll.CoolerON()
        return ERROR_CODE[error]

    def CoolerOFF(self):
        """
        Switches OFF the Cooling. In most models, the camera slowely warms the detector to 0C making sure it is slow.
        WARNING! The camera MUST be warmer than -20C before you call ShutDown otherwise detector will be damaged!
        """
        error = self.dll.CoolerOFF()
        return ERROR_CODE[error]

    def GetTemperature(self):
        ctemperature = c_int()
        error = self.dll.GetTemperature(byref(ctemperature))
        self.temperature = ctemperature.value
        return ERROR_CODE[error]

    def GetTemperatureRange(self):
        c_mintemp = c_int()
        c_maxtemp = c_int()
        error = self.dll.GetTemperatureRange(byref(c_mintemp), byref(c_maxtemp))
        self.min_temp = c_mintemp.value
        self.max_temp = c_maxtemp.value
        return ERROR_CODE[error]

    def SetTemperature(self, temperature):
        # ctemperature = c_int(temperature)
        # error = self.dll.SetTemperature(byref(ctemperature))
        error = self.dll.SetTemperature(temperature)
        return ERROR_CODE[error]


    #-------------------------------------------------------------------------
    #  Camera modes - Acquisition
    #-------------------------------------------------------------------------

    # Set acquisition mode

    def SetAcquisitionMode(self, mode):
        error = self.dll.SetAcquisitionMode(mode)
        return ERROR_CODE[error]

    def SetTriggerMode(self, mode):
        error = self.dll.SetTriggerMode(mode)
        return ERROR_CODE[error]


    # Acquisition process

    def StartAcquisition(self):
        error = self.dll.StartAcquisition()
        # self.dll.WaitForAcquisition()   commented out because it doesnt work properly.
        return ERROR_CODE[error]

    def WaitForAcquisition(self):
        error = self.dll.WaitForAcquisition()
        return ERROR_CODE[error]

    def AbortAcquisition(self):
        """
        This Function aborts the current acquisition if one is active.
        Will return "DRV_SUCCESS" if aborted.
        Will return "DRV_IDLE" if it wasn't acquiering.
        """
        error = self.dll.AbortAcquisition()
        return ERROR_CODE[error]

    def CancelWait(self):
        """
        This function restarts the thread which was put to sleep within the "WaitForAcquisition" function.
        Used typically if the software hangs with an unexpected Wait4Ack function.
        """
        error = self.dll.CancelWait()
        return ERROR_CODE[error]

    def GetMostRecentImage(self, imageArray):
        #dim = self.width * self.height
        dim = imageArray.size
        cimageArray = c_int * dim
        cimage = cimageArray()
        error = self.dll.GetMostRecentImage(pointer(cimage), dim)
        self.GetMostRecentImage_error = error
        for i in range(len(cimage)):
            #imageArray.append(cimage[i])
            imageArray[i] = cimage[i]
        self.imageArray = imageArray[:]
        return ERROR_CODE[error]

    


    # Exposure time control

    def SetExposureTime(self, time):
        error = self.dll.SetExposureTime(c_float(time))
        self.exp_time = time
        return ERROR_CODE[error]

    def GetMaximumExposure(self):
        c_max_exp = c_float()
        error = self.dll.GetMaximumExposure(byref(c_max_exp))
        self.max_exp = c_max_exp.value
        return ERROR_CODE[error]

    def GetAcquisitionTimings(self):
        c_exposure = c_float()
        c_accumulate = c_float()
        c_kinetic = c_float()
        error = self.dll.GetAcquisitionTimings(byref(c_exposure), byref(c_accumulate), byref(c_kinetic))
        self.exp_time = c_exposure.value
        self.accu_cycle_time = c_accumulate.value
        self.kinetic_cycle_time = c_kinetic.value
        return ERROR_CODE[error]

    def EnableKeepCleans(self, mode):
        """
        This function enables or disabeles the keep cleans between trigers. 0=OFF, 1=ON.
        Keep ON unless doing something tricky with the Ext Triggers.
        """
        error = self.dll.EnableKeepCleans(mode)
        return ERROR_CODE[error]

    def SetShutter(self, typ, mode, closingtime, openingtime):
        error = self.dll.SetShutter(typ, mode, closingtime, openingtime)
        return ERROR_CODE[error]

    def SetKineticCycleTime(self, time):  ## for live video mode
        """
        This is the period in seconds between the start of each scan in the series.
        It will set the kinetic cycle time to the nearest valid value not less than the given value.
        The actual time used is obtained by GetAcquisitionTimings().
        """
        error = self.dll.SetKineticCycleTime(c_float(time))
        return ERROR_CODE[error]

    def SetNumberKinetics(self, number):
        number = c_int(number)
        error = self.dll.SetNumberKinetics(number)
        return ERROR_CODE[error]

    def GetSizeOfCircularBuffer(self):
        buff = c_int()
        error = self.dll.GetSizeOfCircularBuffer(byref(buff))
        self.maxbuffersize = buff.value
        return ERROR_CODE[error]

    def SetNumberAccumulations(self, number):
        error = self.dll.SetNumberAccumulations(number)
        return ERROR_CODE[error]

    def SetAccumulationCycleTime(self, acc_time):
        error = self.dll.SetAccumulationCycleTime(c_float(acc_time))
        return ERROR_CODE[error]

    def GetTotalNumberImagesAcquired(self):
        '''
        This function will return the total number of images acquired since the 
        current acquisition started. If the camera is idle the value returned is
        the number of images acquired during the last acquisition.
        '''
        c_nbr_image = c_long()
        error = self.dll.GetTotalNumberImagesAcquired(byref(c_nbr_image))
        self.nbr_images_acquired = c_nbr_image.value
        return ERROR_CODE[error]

    def GetNumberNewImages(self):
        '''
        This function will return information on the number of new images (i.e. 
        images which have not yet been retrieved) in the circular buffer. This 
        information can be used with GetImages to retrieve a series of the latest 
        images. If any images are overwritten in the circular buffer they can no 
        longer be retrieved and the information returned will treat overwritten 
        images as having been retrieved.
        '''
        c_first_Nimages = c_long()
        c_last_Nimages = c_long()
        error = self.dll.GetNumberNewImages(byref(c_first_Nimages), byref(c_last_Nimages))
        self.first_buffer = c_first_Nimages.value
        self.last_buffer = c_last_Nimages.value
        return ERROR_CODE[error]




    #-------------------------------------------------------------------------
    #  Camera modes - Readout images
    #-------------------------------------------------------------------------

    def SetReadMode(self, mode):
        error = self.dll.SetReadMode(mode)
        return ERROR_CODE[error]

    def SetImage(self, hbin, vbin, hstart, hend, vstart, vend):
        error = self.dll.SetImage(hbin, vbin, hstart, hend, vstart, vend)
        return ERROR_CODE[error]

    def SetVSAmplitude(self, voltage):
        error = self.dll.SetVSAmplitude(voltage)
        return ERROR_CODE[error]

    def SetFrameTransferMode(self, mode):
        '''
        This function will set whether an acquisition will readout in Frame Transfer Mode.
        If the acquisition mode is Single Scan or Fast Kinetics this call will have no affect.
        '''
        error = self.dll.SetFrameTransferMode(c_int(mode))
        return ERROR_CODE[error]        

    def SetIsolatedCropMode(self, active, cropheight, cropwidth, vbin, hbin):
        error = self.dll.SetIsolatedCropMode(active, cropheight, cropwidth, vbin, hbin)
        return ERROR_CODE[error]

    def SetMultiTrack(self, number, height, offset, bottom, gap):
        error = self.dll.SetMultiTrack(number, height, offset, bottom, gap)
        return ERROR_CODE[error]

    # Horizontal / Vertical speed

    def SetHSSpeed(self, typ, index):
        error = self.dll.SetHSSpeed(c_int(typ), c_int(index))
        return ERROR_CODE[error]

    def SetVSSpeed(self, index):
        error = self.dll.SetVSSpeed(c_int(index))
        return ERROR_CODE[error]   

    def GetNumberVSSpeeds(self):
        channel  = c_int()
        typ      = c_int()
        speeds   = c_int()
        error   = self.dll.GetNumberVSSpeeds(byref(channel),byref(typ),byref(speeds))
        self.adchannel_vs_speed = channel.value
        self.typ_vs_speed       = typ.value
        self.number_vs_speeds   = speeds.value
        return ERROR_CODE[error]
        
    def GetNumberHSSpeeds(self):
        channel  = c_int()
        typ      = c_int()
        speeds   = c_int()
        error   = self.dll.GetNumberHSSpeeds(byref(channel),byref(typ),byref(speeds))
        self.adchannel_hs_speed = channel.value
        self.typ_hs_speed       = typ.value
        self.number_hs_speeds   = speeds.value
        return ERROR_CODE[error]

    def GetVSSpeed(self):
        index = c_int()
        speed = c_int()
        error = self.dll.GetVSSpeed(byref(index), byref(speed))
        self.index_vs_speed   = index.value
        self.vs_speed         = speed.value
        return ERROR_CODE[error]

    def GetHSSpeed(self):
        index = c_int()
        speed = c_int()
        error = self.dll.GetHSSpeed(byref(index), byref(speed))
        self.index_hs_speed = index.value
        self.hs_speed       = speed.value
        return ERROR_CODE[error]

    def GetNumberVerticalSpeeds(self):
        number  = c_int()
        error   = self.dll.GetNumberVerticalSpeeds(byref(number))
        self.number_vertical_speeds = number.value
        return ERROR_CODE[error]
        
    def GetNumberHorizontalSpeeds(self):
        number  = c_int()
        error   = self.dll.GetNumberHorizontalSpeeds(byref(number))
        self.number_horizontal_speeds = number.value
        return ERROR_CODE[error]

    def GetVerticalSpeed(self):
        index = c_int()
        speed = c_int()
        error = self.dll.GetVerticalSpeed(byref(index), byref(speed))
        self.index_vertical_speed   = index.value
        self.vertical_speed         = speed.value
        return ERROR_CODE[error]

    def GetHorizontalSpeed(self):
        index = c_int()
        speed = c_int()
        error = self.dll.GetHorizontalSpeed(byref(index), byref(speed))
        self.index_horizontal_speed = index.value
        self.horizontal_speed       = speed.value
        return ERROR_CODE[error]

    def SetVerticalSpeed(self, index):
        error = self.dll.SetVerticalSpeed(index)
        return ERROR_CODE[error]

    def SetHorizontalSpeed(self, index):
        error = self.dll.SetHorizontalSpeed(index)
        return ERROR_CODE[error]




    #-------------------------------------------------------------------------
    #  Gain 
    #-------------------------------------------------------------------------

    def GetEMCCDGain(self):
        gain = c_int()
        error = self.dll.GetEMCCDGain(byref(gain))
        self.gain = gain.value
        return ERROR_CODE[error]

    def SetEMCCDGain(self, gain):
        error = self.dll.SetEMCCDGain(gain)
        return ERROR_CODE[error]

    def GetEMGainRange(self):
        low = c_int()
        high = c_int()
        error = self.dll.GetEMGainRange(byref(low), byref(high))
        self.gainRange = (low.value, high.value)
        return ERROR_CODE[error]

    def SetEMGainMode(self, mode):
        error = self.dll.SetEMGainMode(c_int(mode))
        return ERROR_CODE[error]

    def GetNumberPreAmpGains(self):
        noGains = c_int()
        error = self.dll.GetNumberPreAmpGains(byref(noGains))
        self.noGains = noGains.value
        return ERROR_CODE[error]

    def GetPreAmpGain(self):
        gain = c_float()

        self.preAmpGain = []

        for i in range(self.noGains):
            self.dll.GetPreAmpGain(i, byref(gain))
            self.preAmpGain.append(gain.value)

    def SetPreAmpGain(self, index):
        error = self.dll.SetPreAmpGain(index)
        return ERROR_CODE[error]

    def SetOutputAmplifier(self, typ):
        error = self.dll.SetOutputAmplifier(typ)
        error = self.dll.SetOutputAmplifier(typ)
        return ERROR_CODE[error]




    #-------------------------------------------------------------------------
    #  High-order functions (that should not be here...) 
    #-------------------------------------------------------------------------

    #def SetSingleScan(self):
        # self.SetReadMode(4)
        # self.SetAcquisitionMode(1)
        # self.SetImage(1, 1, 1, self.width, 1, self.height)

    def GetAcquiredKineticSeriesData(self, imageArray, numberframes):       
        """
        Returns the data from the last acquisition as 32-bit signed integers.
        """
        dim = self.width * self.height * numberframes
        cimageArray = c_int * dim
        cimage = cimageArray()
        error = self.dll.GetAcquiredData(pointer(cimage), dim)

        for i in range(len(cimage)):
            imageArray.append(cimage[i])

        self.imageArray = imageArray[:]
        return ERROR_CODE[error]

    def SaveAsBmp(self, path):
        im = Image.new("RGB", (512, 512), "white")
        pix = im.load()

        for i in range(len(self.imageArray)):
            (row, col) = divmod(i, self.width)
            picvalue = int(round(self.imageArray[i] * 255.0 / 65535))
            pix[row, col] = (picvalue, picvalue, picvalue)

        im.save(path, "BMP")

    #def SetVideoScan(self):
        # self.SetReadMode(4)
        # self.SetAcquisitionMode(5)

        # self.SetKineticCycleTime(0)
        # self.SetImage(1, 1, 1, self.width, 1, self.height)

    #def SetFrameSeries(self):
        # self.SetReadMode(4)
        # self.SetAcquisitionMode(3)
        # self.SetImage(1, 1, 1, self.width, 1, self.height)

    # def WaitForIdle(self, maxwaittime=10):
    #     t0 = time.time()
    #     while ((time.time() - t0) <= maxwaittime):
    #         time.sleep(0.1)
    #         self.GetStatus()
    #         if self.status == ERROR_CODE[20073]:# 20073: not acquiring
    #             return self.status
    #     return self.status

    # def SetSeriesScanParam(self, N_acc, Nframes, acc_cycle_time, KinCyclTime):
        #"""
        #Sets the Parameters needed for taking a datacube. Number entered needs to be the number of frames.
        #Can also change the kinectic cycle time by writing 'KinCyclTime=##' in (s).
        #"""
        #self.SetReadMode(4)
        #self.SetAcquisitionMode(3)
        #self.SetNumberAccumulations(N_acc)
        #self.SetAccumulationCycleTime(acc_cycle_time)
        #self.SetNumberKinetics(Nframes)
        #self.numberframes = N_acc * Nframes
        #self.SetKineticCycleTime(KinCyclTime)

    #def GetAccumulateCycleTime(self):
    #    self.GetAcquisitionTimings()
    #    return self.accu_cycle_time

    #def GetKinetic(self):
        #self.GetAcquisitionTimings()
        #return self.kinetic_cycle_time





ERROR_CODE = {
    20001: "DRV_ERROR_CODES",
    20002: "DRV_SUCCESS",
    20003: "DRV_VXDNOTINSTALLED",
    20004: "DRV_ERROR_SCAN",
    20005: "DRV_ERROR_CHECK_SUM",
    20006: "DRV_ERROR_FILELOAD",
    20007: "DRV_UNKNOWN_FUNCTION",
    20008: "DRV_ERROR_VXD_INIT",
    20009: "DRV_ERROR_ADDRESS",
    20010: "DRV_ERROR_PAGELOCK",
    20011: "DRV_ERROR_PAGE_UNLOCK",
    20012: "DRV_ERROR_BOARDTEST",
    20013: "DRV_ERROR_ACK",
    20014: "DRV_ERROR_UP_FIFO",
    20015: "DRV_ERROR_PATTERN",
    20017: "DRV_ACQUISITION_ERRORS",
    20018: "DRV_ACQ_BUFFER",
    20019: "DRV_ACQ_DOWNFIFO_FULL",
    20020: "DRV_PROC_UNKNOWN_INSTRUCTION",
    20021: "DRV_ILLEGAL_OP_CODE",
    20022: "DRV_KINETIC_TIME_NOT_MET",
    20023: "DRV_ACCUM_TIME_NOT_MET",
    20024: "DRV_NO_NEW_DATA",
    20026: "DRV_SPOOLERROR",
    20033: "DRV_TEMPERATURE_CODES",
    20034: "DRV_TEMPERATURE_OFF",
    20035: "DRV_TEMPERATURE_NOT_STABILIZED",
    20036: "DRV_TEMPERATURE_STABILIZED",
    20037: "DRV_TEMPERATURE_NOT_REACHED",
    20038: "DRV_TEMPERATURE_OUT_RANGE",
    20039: "DRV_TEMPERATURE_NOT_SUPPORTED",
    20040: "DRV_TEMPERATURE_DRIFT",
    20049: "DRV_GENERAL_ERRORS",
    20050: "DRV_INVALID_AUX",
    20051: "DRV_COF_NOTLOADED",
    20052: "DRV_FPGAPROG",
    20053: "DRV_FLEXERROR",
    20054: "DRV_GPIBERROR",
    20064: "DRV_DATATYPE",
    20065: "DRV_DRIVER_ERRORS",
    20066: "DRV_P1INVALID",
    20067: "DRV_P2INVALID",
    20068: "DRV_P3INVALID",
    20069: "DRV_P4INVALID",
    20070: "DRV_INIERROR",
    20071: "DRV_COFERROR",
    20072: "DRV_ACQUIRING",
    20073: "DRV_IDLE",
    20074: "DRV_TEMPCYCLE",
    20075: "DRV_NOT_INITIALIZED",
    20076: "DRV_P5INVALID",
    20077: "DRV_P6INVALID",
    20078: "DRV_INVALID_MODE",
    20079: "DRV_INVALID_FILTER",
    20080: "DRV_I2CERRORS",
    20081: "DRV_DRV_I2CDEVNOTFOUND",
    20082: "DRV_I2CTIMEOUT",
    20083: "DRV_P7INVALID",
    20089: "DRV_USBERROR",
    20090: "DRV_IOCERROR",
    20091: "DRV_NOT_SUPPORTED",
    20093: "DRV_USB_INTERRUPT_ENDPOINT_ERROR",
    20094: "DRV_RANDOM_TRACK_ERROR",
    20095: "DRV_INVALID_TRIGGER_MODE",
    20096: "DRV_LOAD_FIRMWARE_ERROR",
    20097: "DRV_DIVIDE_BY_ZERO_ERROR",
    20098: "DRV_INVALID_RINGEXPOSURES",
    20099: "DRV_BINNING_ERROR",
    20990: "DRV_ERROR_NOCAMERA",
    20991: "DRV_NOT_SUPPORTED",
    20992: "DRV_NOT_AVAILABLE",
    20115: "DRV_ERROR_MAP",
    20116: "DRV_ERROR_UNMAP",
    20117: "DRV_ERROR_MDL",
    20118: "DRV_ERROR_UNMDL",
    20119: "DRV_ERROR_BUFFSIZE",
    20121: "DRV_ERROR_NOHANDLE",
    20130: "DRV_GATING_NOT_AVAILABLE",
    20131: "DRV_FPGA_VOLTAGE_ERROR",
    20100: "DRV_INVALID_AMPLIFIER",
}
