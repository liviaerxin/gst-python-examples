"""
    GST_PLUGIN_PATH=$GST_PLUGIN_PATH:~/.local/lib/gstreamer-1.0/:$PWD/gst
    PYTHONPATH=$PYTHONPATH:~/Document/my-jetbot
    GST_DEBUG=python:6 gst-launch-1.0 videotestsrc ! 'video/x-raw,format=RGB' ! gstobjectdetection flip=True ! fakesink

    HOST=192.168.31.175
    GST_DEBUG=python:6 gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=60/1,format=NV12' ! nvvidconv ! video/x-raw,format=BGRx,width=1280,height=720 ! videoconvert ! video/x-raw, format=BGR ! gstobjectdetection flip=True ! videoconvert ! omxh264enc insert-sps-pps=true bitrate=16000000 ! rtph264pay ! udpsink port=5000 host=$HOST
"""

import logging
import timeit
import traceback
from typing import Tuple
import time
import cv2
import numpy as np
import os
import time

import threading

from gstreamer import Gst, GObject, GLib, GstBase
from gstreamer.utils import gst_buffer_with_caps_to_ndarray

from trt_ssd_model import TrtSSDModel, draw_bboxes

# from my_camera import CSI_Camera
from my_camera.utils import draw_label

import pycuda.driver as cuda

# model_path = "models/TRT_ssd_mobilenet_v1_coco_2018_01_28.bin"
c_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(
    c_dir, "../../models/TRT_ssd_mobilenet_v2_coco_2018_03_29.bin"
)
print(model_path)
print(f"thread 1: {threading.get_ident()}")


FORMATS = "{RGBx,BGRx,xRGB,xBGR,RGBA,BGRA,ARGB,ABGR,RGB,BGR}"


class GstObjectDetection(GstBase.BaseTransform):

    GST_PLUGIN_NAME = "gstobjectdetection"

    __gstmetadata__ = (
        "GaussianBlur",  # Name
        "Filter",  # Transform
        "Apply Gaussian Blur to Buffer",  # Description
        "Taras Lishchenko <taras at lifestyletransfer dot com>",
    )  # Author

    __gsttemplates__ = (
        Gst.PadTemplate.new(
            "src",
            Gst.PadDirection.SRC,
            Gst.PadPresence.ALWAYS,
            # Set to RGB format
            Gst.Caps.from_string(f"video/x-raw,format={FORMATS}"),
        ),
        Gst.PadTemplate.new(
            "sink",
            Gst.PadDirection.SINK,
            Gst.PadPresence.ALWAYS,
            # Set to RGB format
            Gst.Caps.from_string(f"video/x-raw,format={FORMATS}"),
        ),
    )

    # Explanation: https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#GObject.GObject.__gproperties__
    # Example: https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#properties
    __gproperties__ = {
        # Parameters
        # https://docs.opencv.org/3.0-beta/modules/imgproc/doc/filtering.html#gaussianblur
        "flip": (
            GObject.TYPE_BOOLEAN,
            "bool property",
            "A property that contains bool",
            False,  # default
            GObject.ParamFlags.READWRITE,
        ),
    }

    def __init__(self):

        super(GstObjectDetection, self).__init__()

        # Initialize properties before Base Class initialization
        self.flip = False
        self.tic = 0
        self.fps = 0
        print(f"thread 2: {threading.get_ident()}")

    def do_start(self):
        print(f"thread 3: {threading.get_ident()}")

        return True

    def do_get_property(self, prop: GObject.GParamSpec):
        print(f"thread 4: {threading.get_ident()}")
        if prop.name == "flip":
            return self.flip
        else:
            raise AttributeError("unknown property %s" % prop.name)

    def do_set_property(self, prop: GObject.GParamSpec, value):
        print(f"thread 5: {threading.get_ident()}")
        if prop.name == "flip":
            self.flip = value
        else:
            raise AttributeError("unknown property %s" % prop.name)

    def do_set_caps(self, incaps, outcaps):
        print(f"thread 6: {threading.get_ident()}")
        struct = incaps.get_structure(0)
        self.width = struct.get_int("width").value
        self.height = struct.get_int("height").value

        self.cuda_ctx = cuda.Device(0).make_context()
        self.model = TrtSSDModel(model_path)
        return True

    def do_transform_ip(self, buffer: Gst.Buffer) -> Gst.FlowReturn:
        print(f"thread 7: {threading.get_ident()}")
        try:
            # convert Gst.Buffer to np.ndarray
            image = gst_buffer_with_caps_to_ndarray(
                buffer, self.sinkpad.get_current_caps()
            )
            # print(image.shape)

            # apply flip
            if self.flip == True:
                image[:] = np.flipud(image)

            # apply object detection
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes, confs, clss = self.model(img)
            draw_bboxes(image, boxes, confs, clss)
            draw_label(image, f"Frames Displayed (PS): {self.fps}", (10, 20))
            # draw_label(image, f"Frames Read (PS): {camera.last_frames_read}", (10,40))

            toc = time.time()
            self.fps = 1 / (toc - self.tic)
            print(f"{self.fps}fps")
            self.tic = toc

        except Exception as e:
            logging.error(e)

        return Gst.FlowReturn.OK

    def __del__(self):
        del self.model
        self.model = None
        self.cuda_ctx.pop()
        del self.cuda_ctx


# Required for registering plugin dynamically
# Explained:
# http://lifestyletransfer.com/how-to-write-gstreamer-plugin-with-python/
GObject.type_register(GstObjectDetection)
__gstelementfactory__ = (
    GstObjectDetection.GST_PLUGIN_NAME,
    Gst.Rank.NONE,
    GstObjectDetection,
)
