################################################################################
##################      ANDOR iXon Live Viewer Control      ####################
################################################################################

import numpy as np
import time
import datetime
import zmq
from astropy.io import fits
from threading import Thread
import sys
import gc
from subprocess import call
import os
from tqdm import tqdm

from andor_science import ERROR_CODE
import andor_science as andors


try:
    # import __builtin__ as builtins
    raw_input
except NameError:
    # Python 3
    # import builtins
    raw_input = input


################################################################################
##################              Global variable             ####################
################################################################################


SAVEFILEPATH = '/home/first/Documents/Data/'

DEFAULT_EXP_TIME = 0.001


################################################################################
##################        AndorCtrl class defintion         ####################
################################################################################


class AndorCtrl(Thread):
    def __init__(self, publisher):
        Thread.__init__(self)

        self.pub = publisher

        self.running = True
        self.data_ready = False
        self.live_pause = False

        self.width = 512
        self.height = 512
        self.cam = None

        self.data = np.zeros([self.width, self.height])
        self.dark = np.zeros([self.width, self.height])
        self.rawdark = []

        self.c_min = None
        self.c_max = None

        self.graphpoints = 200

        self.PLTxdata = np.array([])
        self.PLTydata = np.array([])

        self.CROPsize = 3
        self.CROPpos = [0, self.CROPsize * 2, 0, self.CROPsize * 2]
        self.CROPdata = np.zeros([self.CROPsize * 2, self.CROPsize * 2])

        self.lastPhotArrayTRY = []
        self.lastPhotArraySent = []

        self.FLUX_V2PM = None
        self.FLUX_P2VM = None

    def run(self):
        while self.running:
            if not self.live_pause:
                self.rawdata = []
                self.cam.GetMostRecentImage(self.rawdata)
                self.data = np.reshape(self.rawdata, (512,512)) - self.dark

            self.data_ready = True

    def update(self):
        if self.data_ready:
            #self.data_ready = False
            return self.data

    def set_camera(self, camera):
        '''
        This command lets the live viewer (video display tread) know which camera it is talking to.
        This function probably shouldnt be changed, but can be modified if we wish to use the same code
         for different cameras.
         It also passess all the dll camera commands into the viewer so the camera can be controlled from this thread.
        '''
        self.cam = camera

    def set_clims(self, c_min, c_max):
        '''
        Function to set the colour limits of the andor video display.
        Format:
            set_clims(intiger1, intiger2) - 2>1 always otherwise will give error.

        Example:
            a.set_clims(0,10000) - locks between 0 and 10k counts

        To make auto scaling colourmap, set both variables to 'None'
            a.set_clims(None,None)


        The video display should update in realtime your changes.
        '''
        if c_min > c_max:
            raise ValueError("c_min > c_max, c_max has to be higher than c_min.")

        self.c_min = c_min
        self.c_max = c_max

    def set_exptime(self, exptime):
        '''
        Sets the camera exposure time in SECONDS.

        Example:
            a.set_exptime(0.01)

        the default exposure time at initialisation is set by a global variable:
        DEFAULT_EXP_TIME
        and is set to 0.001 - 1ms (1kHz)

        Executing this command will pause the video link while it updates then reactivate it.

        *WARNING* - Careful when subtracting darks as they will no longer match.
        '''
        self.cam.GetMaximumExposure()
        #self.pub.pprint("The maximum exposure time is %f s." % self.cam.max_exp)

        self.cam.AbortAcquisition()
        time.sleep(0.5)
        self.cam.SetExposureTime(exptime)
        time.sleep(0.5)
        self.cam.SetVideoScan()
        time.sleep(0.2)
        self.cam.StartAcquisition()
        time.sleep(0.2+exptime)
        #self.set_shutter_CLOSED()
        #self.acq_new_dark()
        #self.set_shutter_OPEN()
        #self.pub.pprint("A dark for a new exposure time has been taken.\n")

    def get_exptime(self):
        exp_time = self.cam.GetExpTime()
        return exp_time

    def acq_new_dark(self):
        '''
        Acquires a new dark frame for automatic subtraction on the video feed.
        The Dark is taken of whatever is on the detector at the time so make sure you turn the source off.

        Example:
            a.acq_new_dark()

        This should be re-taken whenever you change exposure time.

        It will pause the video feed while it does this and keep it internally in a variable called 'a.dark'
        '''
        self.cam.AbortAcquisition()
        time.sleep(0.5)
        self.rawdark = []

        self.cam.SetSingleScan()
        self.cam.StartAcquisition()
        time.sleep(0.2)
        self.cam.GetMostRecentImage(self.rawdark)
        self.dark = np.reshape(self.rawdark, (512, 512))
        self.cam.AbortAcquisition()

        self.cam.SetVideoScan()
        time.sleep(0.2)
        self.cam.StartAcquisition()
        time.sleep(0.2)

    def set_shutter_CLOSED(self):
        '''
        Sets the internal camera shutter to CLOSED position
        '''
        self.cam.AbortAcquisition()
        time.sleep(0.5)
        self.cam.SetShutter(0, 2, 300, 100)
        time.sleep(0.5)
        self.cam.StartAcquisition()

    def set_shutter_OPEN(self):
        '''
        Sets the internal camera shutter to OPEN position
        '''
        self.cam.AbortAcquisition()
        time.sleep(0.5)
        self.cam.SetShutter(0, 1, 300, 100)
        time.sleep(0.5)
        self.cam.StartAcquisition()

    def GetCurrentTemperature(self):
        self.cam.GetTemperature()
        self.pub.pprint("Current temperature is: " + str(self.cam.temperature) + "°C\n")
        return 0

    def SetDetTemperature(self, temperature):
        self.cam.GetTemperatureRange()
        if temperature < self.cam.min_temp or temperature > self.cam.max_temp:
            self.pub.pprint("!!!Wrong temperature set!!!")
            self.pub.pprint("Set it again.")
            self.pub.pprint("Valid temperature is in the range [%d, %d].\n" % (self.cam.min_temp, self.cam.max_temp))
            return 0

        self.cam.SetTemperature(temperature)

    def get_AcquisitionTimings(self):
        self.cam.GetAcquisitionTimings()
        self.pub.pprint("Actual exposure time is: " + str(self.cam.exp_time))
        self.pub.pprint("Actual accumulation cycle time is: " + str(self.cam.accu_cycle_time))
        self.pub.pprint("Actual kinetic cycle time time is: " + str(self.cam.kinetic_cycle_time))

    def AcqCube(self, N_frames, exptime, filename=None):
        self.set_exptime(exptime)
        imCube   = np.zeros((N_frames, self.cam.height, self.cam.width))
        count = 0
        #while count < N_frames:
        for i in tqdm(range(N_frames)):
            img=[]
            self.cam.GetMostRecentImage(img)
            getimerr = self.cam.GetMostRecentImage_error
            if getimerr == 20002:
                imCube[count,:,:] = np.transpose(np.reshape(self.cam.imageArray, (512, 512)))
                count = count+1
                time.sleep(0.1+exptime)

        if filename is None:
            final_filename = str(int(1000 * time.time())) + "_datacube"
        else:
            final_filename = filename

        self.pub.pprint('Acquisition over...')
        header = fits.Header()
        header['ExpTime'] = np.round(exptime, decimals=3)
        header['Gain'] = self.cam.gain
        header['Temp'] = self.cam.temperature
        fits.writeto(SAVEFILEPATH + final_filename + '.fits', imCube, header, overwrite=True)
        self.pub.pprint("Image saved in '" + SAVEFILEPATH + final_filename + ".fits'\n")

        os.system("ds9 " + SAVEFILEPATH + final_filename + ".fits &")


    def play(self):
        self.live_pause = False

    def pause(self):
        self.live_pause = True

    def start(self):
        '''
        Starts the video display.
        '''
        if self.cam is None:
            raise Exception("Camera not connected!")

        self.cam.SetExposureTime(DEFAULT_EXP_TIME)
        self.cam.SetVideoScan()
        self.cam.SetShutter(0, 1, 300, 100)

        self.cam.GetEMGainRange()
        self.cam.GetEMCCDGain()

        self.pub.pprint("\n")
        self.pub.pprint("Camera Gain: ")
        self.pub.pprint(str(self.cam.gain))
        self.cam.GetNumberPreAmpGains()
        self.cam.GetPreAmpGain()
        self.cam.GetStatus()
        self.cam.StartAcquisition()
        super().start()

        self.pub.pprint("Andor iXon Initialised\n")

    def stop(self):
        self.running = False
        # camera.AbortAcquisition()
        # camera.SetShutter(0,2,300,100)
        # camera.ShutDown()
        self.join()