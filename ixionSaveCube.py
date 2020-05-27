##### acqu_cube function
import sys
import os
import numpy as np
import time
from astropy.io import fits
from pyMilk.interfacing.isio_shmlib import SHM 



#def get(N_frames, exptime, gain, temperature, filename=None):

N_frames 		= np.int(sys.argv[1])
exptime  		= np.float32(sys.argv[2])
gain 			= np.int(sys.argv[3])
temperature 	= np.int(sys.argv[4])
file_name   	= sys.argv[5]
SAVEFILEPATH 	= sys.argv[6]


print(str(N_frames)+' Frames')
print(str(exptime)+' ms')

# Defines the shared mem where the images are + create image cube
im = SHM('ixionim')
imCube = im.multi_recv_data(N_frames, outputFormat=1)
#imCube = np.array(imCube)

print('Cube acquisition over...')

# Save and display the cube
header = fits.Header()
header['ExpTime'] = np.round(exptime, decimals=3)
header['Gain'] = gain
header['Temp'] = temperature
fits.writeto(SAVEFILEPATH + file_name + '.fits', imCube, header, overwrite=True)
print("Image saved in '" + SAVEFILEPATH + file_name + ".fits'\n")

os.system("ds9 " + SAVEFILEPATH + file_name + ".fits &")


