"""
    export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD
    GST_DEBUG=python:6 gst-launch-1.0 videotestsrc ! "video/x-raw,format=RGB" ! gstflip flip=True ! fakesink

    
    HOST=192.168.31.175
    GST_DEBUG=python:6 gst-launch-1.0 videotestsrc! "video/x-raw,format=RGB,width=300,height=200" ! gstflip flip=True ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! rtph264pay ! udpsink port=5000 host=$HOST
"""

import logging
import timeit
import traceback
from typing import Tuple
import time
import cv2
import numpy as np

from gstreamer import Gst, GObject, GLib, GstBase
from gstreamer.utils import gst_buffer_with_caps_to_ndarray


DEFAULT_KERNEL_SIZE = 3
DEFAULT_SIGMA_X = 1.0
DEFAULT_SIGMA_Y = 1.0


def gaussian_blur(img: np.ndarray, kernel_size: int = 3, sigma: Tuple[int, int] = (1, 1)) -> np.ndarray:
    """ Blurs image
    :param img: [height, width, channels >= 3]
    :param kernel_size:
    :param sigma: (int, int)
    """
    sigmaX, sigmaY = sigma
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), sigmaX=sigmaX, sigmaY=sigmaY)


FORMATS = "{RGBx,BGRx,xRGB,xBGR,RGBA,BGRA,ARGB,ABGR,RGB,BGR}"


class GstFlip(GstBase.BaseTransform):

    GST_PLUGIN_NAME = 'gstflip'

    __gstmetadata__ = ("GaussianBlur",  # Name
                       "Filter",   # Transform
                       "Apply Gaussian Blur to Buffer",  # Description
                       "Taras Lishchenko <taras at lifestyletransfer dot com>")  # Author

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            # Set to RGB format
                                            Gst.Caps.from_string(f"video/x-raw,format={FORMATS}")),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            # Set to RGB format
                                            Gst.Caps.from_string(f"video/x-raw,format={FORMATS}")))

    # Explanation: https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#GObject.GObject.__gproperties__
    # Example: https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#properties
    __gproperties__ = {

        # Parameters from cv2.gaussian_blur
        # https://docs.opencv.org/3.0-beta/modules/imgproc/doc/filtering.html#gaussianblur
        "flip": (GObject.TYPE_BOOLEAN,
                      "bool property",
                      "A property that contains bool",
                      False,  # default
                      GObject.ParamFlags.READWRITE
                      ),

    }

    def __init__(self):

        super(GstFlip, self).__init__()

        # Initialize properties before Base Class initialization
        self.flip = False
        
    def do_get_property(self, prop: GObject.GParamSpec):
        if prop.name == 'flip':
            return self.flip
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_set_property(self, prop: GObject.GParamSpec, value):
        if prop.name == 'flip':
            self.flip = value
        else:
            raise AttributeError('unknown property %s' % prop.name)

    def do_transform_ip(self, buffer: Gst.Buffer) -> Gst.FlowReturn:
        try:
            # convert Gst.Buffer to np.ndarray
            image = gst_buffer_with_caps_to_ndarray(buffer, self.sinkpad.get_current_caps())
            print(image.shape)
            # apply gaussian blur to image
            image[:] = np.flipud(image)
            #image[:] = gaussian_blur(image, self.kernel_size, sigma=(self.sigma_x, self.sigma_y))
        except Exception as e:
            logging.error(e)

        return Gst.FlowReturn.OK


# Required for registering plugin dynamically
# Explained:
# http://lifestyletransfer.com/how-to-write-gstreamer-plugin-with-python/
GObject.type_register(GstFlip)
__gstelementfactory__ = (GstFlip.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, GstFlip)

