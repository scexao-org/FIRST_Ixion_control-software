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

## Shared memory package
from pyMilk.interfacing.isio_shmlib import SHM 


################################################################################
##################              Global variable             ####################
################################################################################


SAVEFILEPATH = '/home/first/Documents/FIRST-DATA/'

DEFAULT_EXP_TIME = 0.001


################################################################################
##################        AndorCtrl class defintion         ####################
################################################################################


class AndorCtrl(Thread):

    def __init__(self, camera, publisher):
        Thread.__init__(self)

        self.pub            = publisher
        self.cam            = camera

        self.running        = True
        self.data_ready     = False
        self.live_pause     = False

        self.width          = 512
        self.height         = 100

        self.data           = np.zeros([self.height, self.width])
        self.dark           = np.zeros([self.width, self.height])
        self.rawdark        = []

        self.c_min          = None
        self.c_max          = None

        self.graphpoints    = 200

        self.PLTxdata       = np.array([])
        self.PLTydata       = np.array([])

        self.CROPsize       = 3
        self.CROPpos        = [0, self.CROPsize * 2, 0, self.CROPsize * 2]
        self.CROPdata       = np.zeros([self.CROPsize * 2, self.CROPsize * 2])

        self.lastPhotArrayTRY   = []
        self.lastPhotArraySent  = []

        self.FLUX_V2PM      = None
        self.FLUX_P2VM      = None

        ## Create shared memories for images and darks
        self.ixionim        = SHM('ixionim',   ((self.width, self.height), np.float32), location = -1, shared = 1)
        self.ixiondark      = SHM('ixiondark', ((self.width, self.height), np.float32), location = -1, shared = 1)


    def run(self):
        while self.running:
            if not self.live_pause:
                self.rawdata = np.zeros([self.width*self.height], dtype=np.float32)
                self.cam.GetMostRecentImage(self.rawdata)
                self.data = np.reshape(self.cam.imageArray, (self.height,self.width))# - self.dark

                ## Write the image in the shared memory
                self.ixionim.set_data(self.data.astype(np.float32))

            self.data_ready = True

    def update(self):
        if self.data_ready:
            #self.data_ready = False
            return self.data

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

    def wait_for_idle(self, maxwaittime=10):
        t0 = time.time()
        while ((time.time() - t0) <= maxwaittime):
            time.sleep(0.1)
            self.cam.GetStatus()
            if self.cam.status == "DRV_IDLE":# 20073: not acquiring
                return self.cam.status
        return self.cam.status

    def set_camera(self, camera):
        '''
        This command lets the live viewer know which camera to talk to.
        This function probably shouldn't be changed, but can be modified 
        if we whish to use the same code for different camera.
        It also passess all the dll camera commands into the viewer so the
        camera can be controlled from this thread.
        '''
        self.cam = camera


    #-------------------------------------------------------------------------
    #  Start / Stop live camera
    #-------------------------------------------------------------------------

    def play(self):
        #
        self.live_pause = False

    def pause(self):
        #
        self.live_pause = True

    def start_cropmode(self):
        '''
        Starts the video display.
        '''
        if self.cam is None:
            raise Exception("Camera not connected!")

        self.cam.SetReadMode(4)
        self.cam.SetAcquisitionMode(5)

        self.cam.SetKineticCycleTime(0)
        self.cam.SetIsolatedCropMode(1, self.height, self.width, 1,1)
        self.cam.SetImage(1, 1, 1, self.height, 1, self.width)

        self.cam.SetShutter(0, 1, 50, 50)
        self.cam.SetExposureTime(DEFAULT_EXP_TIME)


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

    def start(self):
        '''
        Starts the video display.
        '''
        if self.cam is None:
            raise Exception("Camera not connected!")

        self.cam.SetExposureTime(DEFAULT_EXP_TIME)
        self.set_video_scan()
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


    #-------------------------------------------------------------------------
    #  Temperature control
    #-------------------------------------------------------------------------

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


    #-------------------------------------------------------------------------
    #  Acquisition Mode
    #-------------------------------------------------------------------------

    def set_single_scan(self):
        '''
        Set the acquisition mode to "Fixed" (takes one image).
        '''
        #self.cam.SetSingleScan()
        self.cam.SetReadMode(4)
        self.cam.SetAcquisitionMode(1)

        self.cam.SetImage(1, 1, 1, self.width, 1, self.height)

    def set_video_scan(self):
        '''
        Set the acquisition mode to "Continuous" (takes one image).
        '''
        self.cam.SetReadMode(4)
        self.cam.SetAcquisitionMode(5)

        self.cam.SetKineticCycleTime(0)
        self.cam.SetImage(1, 1, 1, self.height, 1, self.width)



        #self.cam.SetVideoScan()
    
    def set_frame_series(self):
        self.cam.SetReadMode(4)
        self.cam.SetAcquisitionMode(3)
        self.cam.SetImage(1, 1, 1, self.width, 1, self.height)

    def set_series_scan_param(self, N_acc, Nframes, acc_cycle_time, KinCyclTime):
        """
        Sets the Parameters needed for taking a datacube. Number entered needs to be the number of frames.
        Can also change the kinectic cycle time by writing 'KinCyclTime=##' in (s).
        """
        self.cam.SetReadMode(4)
        self.cam.SetAcquisitionMode(3)
        self.cam.SetNumberAccumulations(N_acc)
        self.cam.SetAccumulationCycleTime(acc_cycle_time)
        self.cam.SetNumberKinetics(Nframes)
        self.numberframes = N_acc * Nframes
        self.cam.SetKineticCycleTime(KinCyclTime)

    def get_AcquisitionTimings(self):
        self.cam.GetAcquisitionTimings()
        self.pub.pprint("Actual exposure time is: " + str(self.cam.exp_time))
        self.pub.pprint("Actual accumulation cycle time is: " + str(self.cam.accu_cycle_time))
        self.pub.pprint("Actual kinetic cycle time time is: " + str(self.cam.kinetic_cycle_time))

    ## ADD MULTI-TRACK and RANDOM-TRACK FUNCTIONS HERE
    ## in progress...

    def set_multi_track(self, number, height, offset, bottom, gap):
        self.cam.SetReadMode(1)
        self.cam.SetMultiTrack(number, height, offset, bottom, gap)

    #-------------------------------------------------------------------------
    #  Exposure time
    #-------------------------------------------------------------------------

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
        self.set_video_scan()
        time.sleep(0.2)
        self.cam.StartAcquisition()
        time.sleep(0.2+exptime)
        #self.set_shutter_CLOSED()
        #self.acq_new_dark()
        #self.set_shutter_OPEN()
        #self.pub.pprint("A dark for a new exposure time has been taken.\n")

    def get_exptime(self):
        #exp_time = self.cam.GetExpTime()
        self.cam.GetAcquisitionTimings()
        self.pub.pprint("Exposure time is %f s." % self.cam.exp_time)
        return self.cam.exp_time


    #-------------------------------------------------------------------------
    #  Horizontal / Vertical speed
    #-------------------------------------------------------------------------

    def get_number_vs_speeds(self):
        self.cam.GetNumberVSSpeeds()
        self.number_vs_speeds = self.cam.number_vs_speeds
        self.pub.pprint("Number of vs speeds is %d.\n" % self.number_vs_speeds)

    def get_number_hs_speeds(self):
        self.cam.GetNumberHSSpeeds()
        self.number_hs_speeds = self.cam.number_hs_speeds
        self.pub.pprint("Number of hs speeds is %d.\n" % self.number_hs_speeds)

    def get_vs_speed(self):
        self.cam.GetVSSpeed()
        self.vs_speed         = self.cam.vs_speed
        self.pub.pprint("VS speed is %d.\n" % self.vs_speed)

    def get_hs_speed(self):
        self.cam.GetHSSpeed()
        self.hs_speed         = self.cam.hs_speed
        self.pub.pprint("HS speed is %d.\n" % self.hs_speed)

    def set_vs_speed(self, index):
        #
        self.cam.SetVSSpeed(index)

    def set_hs_speed(self, index):
        #
        self.cam.SetHSSpeed(index)

    def get_number_vertical_speeds(self):
        self.cam.GetNumberVerticalSpeeds()
        self.number_vertical_speeds = self.cam.number_vertical_speeds
        self.pub.pprint("Number of vertical speeds is %d.\n" % self.number_vertical_speeds)

    def get_number_horizontal_speeds(self):
        self.cam.GetNumberHorizontalSpeeds()
        self.number_horizontal_speeds = self.cam.number_horizontal_speeds
        self.pub.pprint("Number of horizontal speeds is %d.\n" % self.number_horizontal_speeds)

    def get_vertical_speed(self):
        self.cam.GetVerticalSpeed()
        self.index_vertical_speed   = self.cam.index_vertical_speed
        self.vertical_speed         = self.cam.vertical_speed
        self.pub.pprint("Vertical speed index is %d.\n" % self.index_vertical_speed)
        self.pub.pprint("Vertical speed is %d.\n" % self.vertical_speed)

    def get_horizontal_speed(self):
        self.cam.GetHorizontalSpeed()
        self.index_horizontal_speed = self.cam.index_horizontal_speed
        self.horizontal_speed       = self.cam.horizontal_speed
        self.pub.pprint("Horizontal speed index is %d.\n" % self.index_horizontal_speed)
        self.pub.pprint("Horizontal speed is %d.\n" % (self.horizontal_speed))

    def set_vertical_speed(self, index):
        #
        self.cam.SetVerticalSpeed(index)

    def set_horizontal_speed(self, index):
        #
        self.cam.SetHorizontalSpeed(index)




    #-------------------------------------------------------------------------
    #  Display options
    #-------------------------------------------------------------------------

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


    #-------------------------------------------------------------------------
    #  Data / Darks acquisition
    #-------------------------------------------------------------------------

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

        self.set_single_scan()
        self.cam.StartAcquisition()
        time.sleep(0.2)
        self.cam.GetMostRecentImage(self.rawdark)
        self.dark = np.reshape(self.rawdark, (self.height, self.width))
        self.cam.AbortAcquisition()
        self.ixiondark.set_data(self.dark.astype(np.float32))

        self.set_video_scan()
        time.sleep(0.2)
        self.cam.StartAcquisition()
        time.sleep(0.2)



    def acq_cube(self, N_frames, exptime, filename=None):
        self.set_exptime(exptime)
        ## WARNIING : WIDTH AND HEIGHT HAVE BEEN SWAPPED BECAUSE I TAKE TRANSPOSE OF EACH IMAGE
        #imCube   = np.zeros((N_frames, self.width, self.height)) 
        #count = 0
        #while count < N_frames:
        imCube = []
        for i in tqdm(range(N_frames)):
            img = np.zeros([self.width*self.height])
            self.cam.GetMostRecentImage(img)
            #img=[]
            #self.cam.GetMostRecentImage(img)
            getimerr = self.cam.GetMostRecentImage_error
            if getimerr == 20002:
                #imCube[count,:,:] = np.transpose(np.reshape(self.cam.imageArray, (self.height, self.width)))
                imCube.append(np.transpose(np.reshape(self.cam.imageArray, (self.height, self.width))))
                #count = count+1
                time.sleep(0.1+exptime)
        imCube = np.array(imCube)

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
