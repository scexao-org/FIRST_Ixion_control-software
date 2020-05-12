
def QuickCube2(self, N_cubes, N_frames, exptime, filename=None):
        #time.sleep(0.5)
        
        self.cam.SetExposureTime(exptime)

        self.pause()
        self.cam.AbortAcquisition()
        #time.sleep(0.1)
        self.cam.FreeInternalMemory()
        #time.sleep(0.2)
        self.cam.SetAcquisitionMode(3)
        #time.sleep(0.2)
        #self.cam.SetNumberAccumulations(1)
        Cycle = N_cubes * N_frames * exptime
        #self.cam.SetAccumulationCycleTime(Cycle)
        self.cam.SetNumberKinetics(N_frames)
        #time.sleep(0.2)

        #self.SetKineticCycleTime(KinCyclTime)
        rawimage = []
        self.cam.StartAcquisition()

        time.sleep((exptime*N_frames)*10)
        ## 50 --> okay for 25 frames of 0.02sec // 50 frames of 0.01sec
        ## ? 100 de 5ms ? yes
        #self.set_exptime(exptime)
        
        
        
        

        # timecheck = time.time()
        # while self.cam.status == ERROR_CODE[20072]:
        #     self.cam.GetStatus()
        #     self.pub.pprint(str(self.cam.status)+"\n")
        #     #self.cam.GetTotalNumberImagesAcquired()
        #     #self.pub.pprint(str(self.cam.nbr_images_acquired))
        #     time.sleep(exptime*N_frames)

        #     if time.time() - timecheck > 10 :  #CHANGE BACK TO 20!!!!
        #         self.pub.pprint("time " + str(self.cam.status))
        #         timecheck = time.time()
        #         self.cam.AbortAcquisition() # if you go more than 20 seconds, kill yourself
        #         break

        #self.cam.GetTotalNumberImagesAcquired()
        #self.pub.pprint(str(self.cam.nbr_images_acquired))

        #self.cam.GetNumberNewImages()
        #self.pub.pprint(str(self.cam.first_buffer) + "-" + str(self.cam.last_buffer))

        self.cam.GetAcquiredKineticSeriesData(rawimage, N_frames)
        #self.cam.GetMostRecentImage(rawimage)
        Data_finale = np.transpose(np.reshape(rawimage, (N_frames,512, 512)), axes=(0,2,1))

        #self.cam.GetNumberNewImages()
        #self.pub.pprint(str(self.cam.first_buffer) + "-" + str(self.cam.last_buffer))

        #self.cam.GetTotalNumberImagesAcquired()
        #self.pub.pprint(str(self.cam.nbr_images_acquired))
        self.cam.GetStatus()
        self.pub.pprint(self.cam.status)
        #time.sleep(2)

        #if filename is None:
        #    filename = str(int(1000 * time.time())) + "_takeframe"
        
        # Set the fits file name of one data cube
        if filename is None:
            final_filename = str(int(1000 * time.time())) + "_datacube"
        else:
            final_filename = filename
        hdu = fits.PrimaryHDU(Data_finale)
        hdul = fits.HDUList([hdu])

        self.cam.GetEMCCDGain()
        self.cam.GetTemperature()

        # Set the header of the fits file
        header = fits.Header()
        header['Exp_Time (s)'] = np.round(exptime, decimals=3)
        header['EMCCD gain'] = self.cam.gain
        header['CCD temp (Cent)'] = self.cam.temperature
        fits.writeto(SAVEFILEPATH + final_filename + '.fits', Data_finale, header, overwrite=True)
        self.pub.pprint("Image saved in '" + SAVEFILEPATH + final_filename + ".fits'\n")

        # Get back to the live feed
        #self.cam.SetVideoScan()
        #self.cam.StartAcquisition()
        #self.play()
        #time.sleep(2)

        os.system("ds9 " + SAVEFILEPATH + final_filename + ".fits &")

        # Save a txt file with informations in it
        if filename is None:
                txt_filename = final_filename + "_README"
        else:
            txt_filename = filename + "_README"

        with open(SAVEFILEPATH + txt_filename + ".txt", 'a') as txt_file:
            txt_file.write(str(datetime.datetime.now()) + "\n")
            txt_file.write("Number of frames per cube: " + str(N_frames) + "\n")
            txt_file.write("Exposure time (s): " + str(np.round(exptime, decimals=3)) + "\n")
            txt_file.write("EMCCD gain: " + str(self.cam.gain) + "\n")

        self.pub.pprint("Info saved in '" + SAVEFILEPATH + txt_filename + ".txt'\n")

        self.pub.pprint("Done\n")

def TakeScienceData2(self, N_c, N_f, expt, file_name):
        #self.cam.SetExposureTime(exptime)
        #self.pause()
        #self.cam.AbortAcquisition()

        #self.pause()
        #self.cam.AbortAc100quisition()

        #collect = gc.collect()
        #self.pub.pprint('Garbage collector : collected '+str(collect)+' objects')
        
        for i in range(N_c):
            name = file_name+'_'+str(i)
            #self.pub.pprint('Acquisition Cube '+str(i+1)+' sur '+str(N_cubes)+'\n')
            self.QuickCube2(N_c, N_f, expt, filename=name)

def BarnabyCube(self, ExpTime, NumFrames, filename, EMCCDgain=0, HSSpeed=0, VSSpeed=0, VSVolts=3):
        self.cam.SetReadMode(4)

        # Set acquisition mode to Kinetic Series and related settings
        self.cam.SetAcquisitionMode(3)
        self.cam.SetExposureTime(ExpTime)
        self.cam.SetNumberAccumulations(1)
        self.cam.SetNumberKinetics(NumFrames)

        # Following line redundant in FrameTransfer mode (depends on exptime, cannot set this in software)
        # self.cam.SetKineticCycleTime(0) #Use shortest possible cycle time

        # Use GetAcquisitionTimings to find actual timings...
        self.cam.SetKineticCycleTime(0.1)

        # Set frame transfer mode to on
        self.cam.SetFrameTransferMode(1)

        # Set trigger mode to internal
        self.cam.SetTriggerMode(0)

        # Set shift speeds (to do)
        self.cam.SetEMGainMode(2) # Believed to be 'real', docs wrong.
        #self.cam.SetEMAdvanced(0) # Set to 1 at your peril!!! (RTFM)
        self.cam.SetEMCCDGain(EMCCDgain)
        self.cam.SetHSSpeed(0, HSSpeed) #Also sets to EM output amp
        self.cam.SetVSSpeed(VSSpeed)
        self.cam.SetVSAmplitude(VSVolts)
        #self.cam.SetFrameTransferMode(1) #Already been called
        #self.cam.SetKineticCycleTime(0) #Already been called

        # Setup image size
        self.cam.SetImage(1,1,1,self.cam.width,1,self.cam.height)

        self.get_AcquisitionTimings()

        # Get the images
        self.cam.SetSpool(1,5,'fitsspool',10)
        self.cam.StartAcquisition()
        # WaitForAcquisition doesn't seem to wait long enough? Use a loop:
        status = 20072 #Initialise with state 'DRV_ACQUIRING'
        while status == 20072:
            self.cam.GetStatus()
            status = self.cam.status
            time.pause(0.01)

        self.pub.pprint('done')
        self.cam.SetSpool(0,5,'fitsspool',10)

def BarnabyCube2(self, ExpTime, NumFrames, filename=None, EMCCDgain=0, HSSpeed=0, VSSpeed=0, VSVolts=3):
        #self.cam.AbortAcquisition()
        #time.sleep(0.1)
        self.cam.SetReadMode(4)

        # Set acquisition mode to Kinetic Series and related settings

        self.cam.exp_time           = ExpTime
        #self.cam.accu_cycle_time    = 1
        self.cam.kinetic_cycle_time = 0.1

        self.cam.SetAcquisitionMode(3)
        self.cam.SetExposureTime(self.cam.exp_time)
        self.cam.SetNumberAccumulations(1)
        self.cam.SetNumberKinetics(NumFrames)

        # Following line redundant in FrameTransfer mode (depends on exptime, cannot set this in software)
        # self.cam.SetKineticCycleTime(0) #Use shortest possible cycle time

        # Use GetAcquisitionTimings to find actual timings...
        self.cam.SetKineticCycleTime(self.cam.kinetic_cycle_time)

        # Set frame transfer mode to on
        self.cam.SetFrameTransferMode(1)

        # Set trigger mode to internal
        self.cam.SetTriggerMode(0)

        # Set shift speeds (to do)
        self.cam.SetEMGainMode(2) # Believed to be 'real', docs wrong.
        #self.cam.SetEMAdvanced(0) # Set to 1 at your peril!!! (RTFM)
        self.cam.SetEMCCDGain(EMCCDgain)
        self.cam.SetHSSpeed(0, HSSpeed) #Also sets to EM output amp
        self.cam.SetVSSpeed(VSSpeed)
        self.cam.SetVSAmplitude(VSVolts)

        self.get_AcquisitionTimings()
        


        imCube   = np.zeros((NumFrames, self.cam.height, self.cam.width))
        #img      = np.zeros(self.cam.height*self.cam.width)
        img      = []
        self.cam.StartAcquisition()
        time.sleep(0.01)
        count    = 0
        status   = 20072     # Initialise with state 'DRV_ACQUIRING'
        getimerr = 20002   # Initialise with state 'DRV_SUCCESS'  
        #self.pub.pprint("testokay")
        while count < NumFrames:#status == 20072 and getimerr == 20002:
            #self.cam.GetStatus()
            self.cam.GetMostRecentImage(img)
            #status   = self.cam.Get_status_error 
            getimerr = self.cam.GetMostRecentImage_error
            #self.pub.pprint(status)
            #self.pub.pprint(4)
            #self.pub.pprint(getimerr)
            if getimerr == 20002:
                imCube[count,:,:] = np.transpose(np.reshape(self.cam.imageArray, (512, 512)))
                count = count+1
                time.sleep(0.1)
                #self.pub.pprint(count)


        if filename is None:
            final_filename = str(int(1000 * time.time())) + "_datacube"
        else:
            final_filename = filename

        self.pub.pprint('Acquisition over...')
        header = fits.Header()
        header['ExpTime'] = np.round(ExpTime, decimals=3)
        header['Gain'] = self.cam.gain
        header['Temp'] = self.cam.temperature
        fits.writeto(SAVEFILEPATH + final_filename + '.fits', imCube, header, overwrite=True)
        self.pub.pprint("Image saved in '" + SAVEFILEPATH + final_filename + ".fits'\n")

        os.system("ds9 " + SAVEFILEPATH + final_filename + ".fits &")








    def QuickCube2(self, N_cubes, N_frames, exptime, filename=None):
        command = "a.QuickCube2(" + str(N_cubes) + "," + str(N_frames) + "," + str(exptime) + ",filename='" + str(filename) + "')"
        self.pub.send_multipart([self.client_adress, command.encode('UTF-8')])

    def TakeScienceData2(self, N_c, N_f, expt, file_name):
        command = "a.TakeScienceData2(" + str(N_c) + "," + str(N_f) + "," + str(expt) + "," + str(file_name) + ")"
        self.pub.send_multipart([self.client_adress, command.encode('UTF-8')])

    def BarnabyCube(self, ExpTime, NumFrames, filename, EMCCDgain=0, HSSpeed=0, VSSpeed=0, VSVolts=3):
        command = "a.BarnabyCube(" + str(ExpTime) + "," + \
                  str(NumFrames) + "," + str(filename) + \
                  ",EMCCDgain=" + str(EMCCDgain) + \
                  ",HSSpeed=" + str(HSSpeed) + \
                  ",VSSpeed=" + str(VSSpeed) + \
                  ",VSVolts=" + str(VSVolts) + ")"
        self.pub.send_multipart([self.client_adress, command.encode('UTF-8')])

    def BarnabyCube2(self, ExpTime, NumFrames, filename=None):#, EMCCDgain=0, HSSpeed=0, VSSpeed=0, VSVolts=3):
        
        command = "a.BarnabyCube2(" + str(ExpTime) + "," + str(NumFrames) + ",filename='" + str(filename)+ "')"# + ",EMCCDgain=" + str(EMCCDgain) + ",HSSpeed=" + str(HSSpeed) + ",VSSpeed=" + str(VSSpeed) +  ",VSVolts=" + str(VSVolts) + ")"
        self.pub.send_multipart([self.client_adress, command.encode('UTF-8')])










































def takequickdatacube(self, Nframes, exposure_time, quickest_mode=False):
        '''
        A faster function of the normal datacube acquisition used in other functions.
        Has less overheads and does not save.
        Be very carefull when running this out of the blue, as it has a lot of checks
        removed so can crash if used outside a function.
        '''
        self.rawcube = []
        self.cube = np.zeros([self.width, self.height, Nframes])

        if not quickest_mode:
            self.pause()
            self.cam.AbortAcquisition()

        self.cam.FreeInternalMemory()

        self.cam.SetSeriesScanParam(Nframes, exposure_time, exposure_time)# Sets to Kinetic Mode with Nframes size.
        self.pub.pprint(self.cam.GetKinetic())


        self.pub.pprint("cube1")
        self.cam.SetImage(1, 1, 1, self.width, 1, self.height)
        # Acquisition
        self.cam.StartAcquisition()
        # Wait untill the acquisition is done
        self.cam.GetStatus()
        timecheck = time.time()
        while self.cam.status == ERROR_CODE[20072]:
            self.cam.GetStatus()
            self.pub.pprint(self.cam.status)
            if time.time() - timecheck > 20:
                self.pub.pprint("time " + str(self.cam.status))
                timecheck = time.time()
                break
        self.pub.pprint(self.cam.status)

        
        # Retrieve the scans
        self.cam.GetAcquiredKineticSeriesData(self.rawcube)
        self.cube = np.reshape(self.rawcube, (Nframes, 512, 512))


        self.cam.AbortAcquisition()
        self.pub.pprint("cube2")


        # Get back to the live feed
        if not quickest_mode:
            self.cam.SetVideoScan()
            self.cam.StartAcquisition()
            self.play()

        return self.cube

    def takedatacube(self, N_cube, N_cube_frames, exposure_time, camera_gain=0, filename=None, **kwargs):
        '''
        Function that will take a cube of images and can save them if needed.
        The function sets the exposure time to be whatever the current exp time is on the video feed.

        Format:
        takedatacube(
            Number of frames in a cube (typically between 1-100) *intiger*,
            save = True/False (tells the function if you want to save the cube as fits),
            filename = String (the filename you want for the datacube)
            header = None (currently set to None, but can pass variables into the fits header this way)
                        )

        Example:
        a.takedatacube(20,save=True, filename='/testfolder/Nicktest1')

        - this will save a fits file called Nicktest1 which has 20 frames taken sequentially
        '''
        # Set the exposure time
        prev_expTime = self.get_exptime()
        self.set_exptime(exposure_time)
        current_expTime = self.get_exptime()

        
        # Set the EMCCD gain
        self.cam.GetEMGainRange()
        if (camera_gain < self.cam.gainRange[0] or camera_gain > self.cam.gainRange[1]) and camera_gain != 0:
            self.pub.pprint("Wrong EMCCD gain. Has to be in [%i, %i]." % (self.cam.gainRange[0], self.cam.gainRange[1]))
            self.pub.pprint("Execute again the function with the appropriate EMCCD gain.\n")
            return 0

        self.cam.SetEMCCDGain(camera_gain)

        self.pause()
        self.cam.AbortAcquisition()


        # Start to take the data cubes
        for cube_i in range(N_cube):
            # Set the fits file name of one data cube
            if filename is None:
                final_filename = str(int(1000 * time.time())) + "_datacube"
            else:
                if cube_i + 1 < 10:
                    final_filename = filename + "_0" + str(cube_i+1)
                else:
                    final_filename = filename + "_" + str(cube_i+1)



            ########
            self.rawcube = []
            self.cube = np.zeros([N_cube, N_cube_frames, self.width, self.height])

            self.cam.SetSeriesScanParam(Nframes, exposure_time, exposure_time + 0.5)# Sets to Kinetic Mode with Nframes size.
            self.pub.pprint(self.cam.GetKinetic())


            self.pub.pprint("cube1")
            # Acquisition
            self.cam.StartAcquisition()
            # Wait untill the acquisition is done
            self.cam.GetStatus()
            timecheck = time.time()
            while self.cam.status == ERROR_CODE[20072]:
                self.cam.GetStatus()
                self.pub.pprint(self.cam.status)
                if time.time() - timecheck > 20:
                    self.pub.pprint("time " + str(self.cam.status))
                    timecheck = time.time()
                    break
            self.pub.pprint(self.cam.status)

            
            # Retrieve the scans
            self.cam.GetAcquiredKineticSeriesData(self.rawcube)
            self.cube = np.reshape(self.rawcube, (Nframes, 512, 512))


            self.cam.AbortAcquisition()
            self.pub.pprint("cube2")


            # Get back to the live feed
            if not quickest_mode:
                self.cam.SetVideoScan()
                self.cam.StartAcquisition()
                self.play()

            #########


            # Take one data cube
            #self.takequickdatacube(N_cube_frames, quickest_mode=True)


            # Save the frame in a fits file
            hdu = fits.PrimaryHDU(self.cube)
            hdul = fits.HDUList([hdu])

            # Set the header of the fits file
            header = fits.Header()
            header['ith_cube'] = cube_i+1
            header['N_frames'] = N_cube_frames
            header['Exp_Time (s)'] = np.round(current_expTime, decimals=3)
            header['EMCCD_Gain'] = camera_gain

            fits.writeto(SAVEFILEPATH + final_filename + ".fits", self.cube, header, overwrite=True)
            self.pub.pprint("Datacube saved in '" + SAVEFILEPATH + final_filename + ".fits'\n")


        # Save a txt file with informations in it
        if filename is None:
                txt_filename = final_filename + "_README"
        else:
            txt_filename = filename + "_README"

        with open(SAVEFILEPATH + txt_filename + ".txt", 'a') as txt_file:
            txt_file.write(str(datetime.datetime.now()) + "\n")
            txt_file.write("Number of cubes: " + str(N_cube) + "\n")
            txt_file.write("Number of frames per cube: " + str(N_cube_frames) + "\n")
            txt_file.write("Exposure time (s): " + str(np.round(current_expTime, decimals=3)) + "\n")
            txt_file.write("EMCCD gain: " + str(camera_gain) + "\n")

            for key in kwargs:
                txt_file.write(str(key) + ": " + str(kwargs[key]) + "\n")

        self.pub.pprint("Info saved under in '" + SAVEFILEPATH + txt_filename + ".txt'\n")


        # Get back to the live feed
        self.cam.SetVideoScan()
        self.cam.StartAcquisition()
        self.play()


        # Put camera settings back
        self.set_exptime(prev_expTime)
        self.cam.SetEMCCDGain(0)

        self.pub.pprint("Data cubes done.\n")

    

    def QuickCube(self, N_cubes, N_frames, exptime, filename=None):
        #time.sleep(0.5)
        
        self.cam.SetExposureTime(exptime)

        self.pause()
        self.cam.AbortAcquisition()
        #time.sleep(0.1)
        self.cam.FreeInternalMemory()
        #time.sleep(0.2)
        self.cam.SetAcquisitionMode(3)
        #time.sleep(0.2)
        #self.cam.SetNumberAccumulations(1)
        Cycle = N_cubes * N_frames * exptime
        #self.cam.SetAccumulationCycleTime(Cycle)
        self.cam.SetNumberKinetics(N_frames)
        #time.sleep(0.2)

        #self.SetKineticCycleTime(KinCyclTime)
        rawimage = []
        self.cam.StartAcquisition()
        
        time.sleep((exptime*N_frames)*4)
        #self.set_exptime(exptime)
        self.cam.GetStatus()
        
        self.pub.pprint(self.cam.status)
        

        # timecheck = time.time()
        # while self.cam.status == ERROR_CODE[20072]:
        #     self.cam.GetStatus()
        #     self.pub.pprint(str(self.cam.status)+"\n")
        #     #self.cam.GetTotalNumberImagesAcquired()
        #     #self.pub.pprint(str(self.cam.nbr_images_acquired))
        #     time.sleep(exptime*N_frames)

        #     if time.time() - timecheck > 10 :  #CHANGE BACK TO 20!!!!
        #         self.pub.pprint("time " + str(self.cam.status))
        #         timecheck = time.time()
        #         self.cam.AbortAcquisition() # if you go more than 20 seconds, kill yourself
        #         break

        #self.cam.GetTotalNumberImagesAcquired()
        #self.pub.pprint(str(self.cam.nbr_images_acquired))

        #self.cam.GetNumberNewImages()
        #self.pub.pprint(str(self.cam.first_buffer) + "-" + str(self.cam.last_buffer))

        self.cam.GetAcquiredKineticSeriesData(rawimage, N_frames)
        #self.cam.GetMostRecentImage(rawimage)
        Data_finale = np.reshape(rawimage, (N_frames,512, 512))

        #self.cam.GetNumberNewImages()
        #self.pub.pprint(str(self.cam.first_buffer) + "-" + str(self.cam.last_buffer))

        #self.cam.GetTotalNumberImagesAcquired()
        #self.pub.pprint(str(self.cam.nbr_images_acquired))

        #time.sleep(2)

        #if filename is None:
        #    filename = str(int(1000 * time.time())) + "_takeframe"
        
        #hdu = fits.PrimaryHDU(Data_finale)
        #hdul = fits.HDUList([hdu])

        # Set the header of the fits file
        #header = fits.Header()
        #header['Exp_Time (s)'] = np.round(exptime, decimals=3)
        #fits.writeto(SAVEFILEPATH + filename + '.fits', Data_finale, header, overwrite=True)
        #self.pub.pprint("Image saved under the name '" + filename + ".fits'\n")

        # Get back to the live feed
        #self.cam.SetVideoScan()
        #self.cam.StartAcquisition()
        #self.play()
        #time.sleep(6)

        self.pub.pprint("Done\n")

    def TakeScienceData(self, N_c, N_f, expt, file_name):
        #self.cam.SetExposureTime(exptime)
        #self.pause()
        #self.cam.AbortAcquisition()

        #self.pause()
        #self.cam.AbortAcquisition()

        #collect = gc.collect()
        #self.pub.pprint('Garbage collector : collected '+str(collect)+' objects')
        
        for i in range(N_c):
            name = file_name+'_'+str(i)
            #self.pub.pprint('Acquisition Cube '+str(i+1)+' sur '+str(N_cubes)+'\n')
            self.QuickCube(N_c, N_f, expt, filename=name)
            collect = gc.collect()
            self.pub.pprint('Garbage collector : collected '+str(collect)+' objects')
            #self.TakeCube(N_frame, exptime, filename=filename+'_'+str(i))

        #self.cam.SetVideoScan()
        #self.cam.StartAcquisition()
        #self.play()

    def TakeCube(self, N_frame, exptime, filename=None):



        self.set_exptime(exptime)

        self.pause()
        self.cam.AbortAcquisition()
        self.cam.SetSingleScan()


        Data_finale = np.zeros([N_frame,512,512])
        self.pub.pprint("Starting Taking Cube\n")
        for i in range(N_frame):
            self.pub.pprint("Frame number :"+str(i))
            #Data_finale[i,:,:]=self.TakeSingleFrame_forCube(exptime)
            rawimage = []
            self.cam.StartAcquisition()

            # Wait untill the acquisition is done
            self.cam.GetStatus()
            while self.cam.status == ERROR_CODE[20072]:
                self.cam.GetStatus()
                self.pub.pprint("Coucou\n")

            # Retrieve the image
            self.cam.GetMostRecentImage(rawimage)
            Data_finale[i,:,:] = np.reshape(rawimage, (512, 512))

            self.cam.AbortAcquisition()

        if filename is None:
            filename = str(int(1000 * time.time())) + "_takeframe"
        hdu = fits.PrimaryHDU(Data_finale)
        hdul = fits.HDUList([hdu])

        # Set the header of the fits file
        header = fits.Header()
        header['Exp_Time (s)'] = np.round(exptime, decimals=3)
        fits.writeto(SAVEFILEPATH + filename + '.fits', Data_finale, header, overwrite=True)
        self.pub.pprint("Image saved under the name '" + filename + ".fits'\n")

        # Get back to the live feed
        self.cam.SetVideoScan()
        self.cam.StartAcquisition()
        self.play()


    def TakeSingleFrame_forCube(self, exptime):
        '''
        Takes a single frame with the current integration time and saves it as a FITS.
        '''
        self.set_exptime(exptime)

        self.pause()
        self.cam.AbortAcquisition()
        self.cam.SetSingleScan()

        
        rawimage = []
        self.cam.StartAcquisition()

        # Wait untill the acquisition is done
        self.cam.GetStatus()
        while self.cam.status == ERROR_CODE[20072]:
            self.cam.GetStatus()
            self.pub.pprint("Coucou\n")

        # Retrieve the image
        self.cam.GetMostRecentImage(rawimage)
        fulldataframe = np.reshape(rawimage, (512, 512))

        self.cam.AbortAcquisition()

        # Get back to the live feed
        self.cam.SetVideoScan()
        self.cam.StartAcquisition()
        self.play()

        
        self.pub.pprint("Frame Taken\n")
        return fulldataframe


    def testcube(self,n_f,exp):
        
        self.pause()
        self.cam.AbortAcquisition()
        self.cam.SetAcquisitionMode(3)
        self.cam.SetExposureTime(exp)
        self.cam.SetNumberKinetics(n_f)
        self.pub.pprint('Begin scan')
        self.cam.StartAcquisition()
        time.sleep((n_f*exp)*4)
        self.cam.GetStatus()
        self.pub.pprint(self.cam.status)
        self.pub.pprint('Done test')
        


    def takeframe(self, exptime=None, filename=None, header=None):
        '''
        Takes a single frame with the current integration time and saves it as a FITS.
        '''
        prev_expTime = self.get_exptime()

        if exptime is not None:
            self.set_exptime(exptime)
        
        current_expTime = self.get_exptime()


        if filename is None:
            filename = str(int(1000 * time.time())) + "_takeframe"


        self.pause()
        self.cam.AbortAcquisition()
        self.cam.SetSingleScan()


        rawimage = []
        self.cam.StartAcquisition()

        # Wait untill the acquisition is done
        self.cam.GetStatus()
        while self.cam.status == ERROR_CODE[20072]:
            self.cam.GetStatus()

        # Retrieve the image
        self.cam.GetMostRecentImage(rawimage)
        fulldataframe = np.reshape(rawimage, (512, 512))

        self.cam.AbortAcquisition()


        # Save the frame in a fits file
        hdu = fits.PrimaryHDU(fulldataframe)
        hdul = fits.HDUList([hdu])

        # Set the header of the fits file
        header = fits.Header()
        header['Exp_Time (s)'] = np.round(current_expTime, decimals=3)
        fits.writeto(SAVEFILEPATH + filename + '.fits', fulldataframe, header, overwrite=True)

        
        # Get back to the live feed
        self.cam.SetVideoScan()
        self.cam.StartAcquisition()
        self.play()

        self.set_exptime(prev_expTime)
        self.pub.pprint("Image saved under the name '" + filename + ".fits'\n")

    def TakeSingleCube(self, N_cube_frames, exposure_time):
        self.pause()
        self.cam.AbortAcquisition()

        # Set the exposure time
        prev_expTime = self.get_exptime()
        self.set_exptime(exposure_time)
        current_expTime = self.get_exptime()
        self.pub.pprint("1")

        self.cam.SetNumberAccumulations(N_cube_frames)
        self.pub.pprint("2")

        acc_cycle_time = exposure_time + 0.5
        self.pub.pprint(acc_cycle_time)
        self.cam.SetAccumulationCycleTime(acc_cycle_time)
        self.pub.pprint("3")
        self.cam.SetAcquisitionMode(2)

        self.cam.StartAcquisition()
        # Wait untill the acquisition is done
        self.cam.GetStatus()
        timecheck = time.time()
        while self.cam.status == ERROR_CODE[20072]:
            self.cam.GetStatus()
            self.pub.pprint(self.cam.status)
            # if time.time() - timecheck > 200000000000:
            #     self.pub.pprint("time " + str(self.cam.status))
            #     timecheck = time.time()
            #     break
        self.pub.pprint(self.cam.status)


        self.cam.WaitForAcquisition()
        self.pub.pprint("5")

        self.rawcube = []
        self.pub.pprint("6")

        self.cam.GetAcquiredKineticSeriesData(self.rawcube, N_cube_frames)
        self.pub.pprint("7")

        self.single_cube = np.reshape(self.rawcube, (N_cube_frames, 512, 512))
        self.pub.pprint("8")

        return self.single_cube

    def TakeDataCube(self, N_cube, N_cube_frames, exposure_time, camera_gain=0, filename=None, **kwargs):
        self.pause()
        self.cam.AbortAcquisition()


        # Set the EMCCD gain
        self.cam.GetEMGainRange()
        if (camera_gain < self.cam.gainRange[0] or camera_gain > self.cam.gainRange[1]) and camera_gain != 0:
            self.pub.pprint("Wrong EMCCD gain. Has to be in [%i, %i]." % (self.cam.gainRange[0], self.cam.gainRange[1]))
            self.pub.pprint("Execute again the function with the appropriate EMCCD gain.\n")
            return 0

        self.cam.SetEMCCDGain(camera_gain)


        for cube_i in range(N_cube):
            # Set the fits file name of one data cube
            if filename is None:
                final_filename = str(int(1000 * time.time())) + "_datacube"
            else:
                if cube_i + 1 < 10:
                    final_filename = filename + "_0" + str(cube_i+1)
                else:
                    final_filename = filename + "_" + str(cube_i+1)

            current_cube = self.TakeSingleCube(N_cube_frames, exposure_time)

            # Save the cube in a fits file
            hdu = fits.PrimaryHDU(current_cube)
            hdul = fits.HDUList([hdu])

            # Set the header of the fits file
            header = fits.Header()
            header['ith_cube'] = cube_i+1
            header['N_frames'] = N_cube_frames
            header['Exp_Time (s)'] = np.round(current_expTime, decimals=3)
            header['EMCCD_Gain'] = camera_gain

            fits.writeto(SAVEFILEPATH + final_filename + ".fits", current_cube, header, overwrite=True)
            self.pub.pprint("Datacube saved in '" + SAVEFILEPATH + final_filename + ".fits'\n")

        # Save a txt file with informations in it
        if filename is None:
                txt_filename = final_filename + "_README"
        else:
            txt_filename = filename + "_README"

        with open(SAVEFILEPATH + txt_filename + ".txt", 'a') as txt_file:
            txt_file.write(str(datetime.datetime.now()) + "\n")
            txt_file.write("Number of cubes: " + str(N_cube) + "\n")
            txt_file.write("Number of frames per cube: " + str(N_cube_frames) + "\n")
            txt_file.write("Exposure time (s): " + str(np.round(current_expTime, decimals=3)) + "\n")
            txt_file.write("EMCCD gain: " + str(camera_gain) + "\n")

            for key in kwargs:
                txt_file.write(str(key) + ": " + str(kwargs[key]) + "\n")

        self.pub.pprint("Info saved under in '" + SAVEFILEPATH + txt_filename + ".txt'\n")


        # Get back to the live feed
        self.cam.AbortAcquisition()
        self.cam.SetVideoScan()
        self.cam.StartAcquisition()
        self.play()


        # Put camera settings back
        self.set_exptime(prev_expTime)
        self.cam.SetEMCCDGain(0)

        self.pub.pprint("Data cubes done.\n")

    def datacubeLM(self, N_cube, N_cube_frames, exposure_time, camera_gain=0, filename=None, **kwargs):
        # Set the exposure time
        prev_expTime = self.get_exptime()
        self.set_exptime(exposure_time)
        current_expTime = self.get_exptime()

        
        # Set the EMCCD gain
        self.cam.GetEMGainRange()
        if (camera_gain < self.cam.gainRange[0] or camera_gain > self.cam.gainRange[1]) and camera_gain != 0:
            self.pub.pprint("Wrong EMCCD gain. Has to be in [%i, %i]." % (self.cam.gainRange[0], self.cam.gainRange[1]))
            self.pub.pprint("Execute again the function with the appropriate EMCCD gain.\n")
            return 0

        self.cam.SetEMCCDGain(camera_gain)

        self.pause()
        self.cam.AbortAcquisition()
        #self.cam.FreeInternalMemory()


        # Start to take the data cubes
        for cube_i in range(N_cube):
            # Set the fits file name of one data cube
            if filename is None:
                final_filename = str(int(1000 * time.time())) + "_datacube"
            else:
                if cube_i + 1 < 10:
                    final_filename = filename + "_0" + str(cube_i+1)
                else:
                    final_filename = filename + "_" + str(cube_i+1)


            # Take one data cube
            self.cube = np.zeros([N_cube_frames, self.width, self.height])
            

            for frame_i in range(N_cube_frames):
                self.cam.SetAcquisitionMode(1)
                self.cam.StartAcquisition()
                self.rawcube = []
                self.cam.GetMostRecentImage(self.rawdata)
                self.cube[frame_i] = np.reshape(self.rawdata, (self.width, self.height))
                self.cam.AbortAcquisition()
                time.sleep(0.025)
            


            # Save the frame in a fits file
            hdu = fits.PrimaryHDU(self.cube)
            hdul = fits.HDUList([hdu])

            # Set the header of the fits file
            header = fits.Header()
            header['ith_cube'] = cube_i+1
            header['N_frames'] = N_cube_frames
            header['Exp_Time (s)'] = np.round(current_expTime, decimals=3)
            header['EMCCD_Gain'] = camera_gain

            fits.writeto(SAVEFILEPATH + final_filename + ".fits", self.cube, header, overwrite=True)
            self.pub.pprint("Datacube saved in '" + SAVEFILEPATH + final_filename + ".fits'\n")


        # Save a txt file with informations in it
        if filename is None:
                txt_filename = final_filename + "_README"
        else:
            txt_filename = filename + "_README"

        with open(SAVEFILEPATH + txt_filename + ".txt", 'a') as txt_file:
            txt_file.write(str(datetime.datetime.now()) + "\n")
            txt_file.write("Number of cubes: " + str(N_cube) + "\n")
            txt_file.write("Number of frames per cube: " + str(N_cube_frames) + "\n")
            txt_file.write("Exposure time (s): " + str(np.round(current_expTime, decimals=3)) + "\n")
            txt_file.write("EMCCD gain: " + str(camera_gain) + "\n")

            for key in kwargs:
                txt_file.write(str(key) + ": " + str(kwargs[key]) + "\n")

        self.pub.pprint("Info saved under in '" + SAVEFILEPATH + txt_filename + ".txt'\n")


        # Get back to the live feed
        self.cam.SetVideoScan()
        self.cam.StartAcquisition()
        self.play()


        # Put camera settings back
        self.set_exptime(prev_expTime)
        self.cam.SetEMCCDGain(0)

        self.pub.pprint("Data cubes done.\n")