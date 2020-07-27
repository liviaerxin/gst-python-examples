#!/usr/bin/env python3

import sys

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True

'''
gst-launch-1.0 -v filesrc location=/home/jetson/Videos/why_I_left_China_for_Good.mp4 ! qtdemux ! h264parse ! omxh264dec ! omxh264enc insert-sps-pps=true ! rtph264pay ! udpsink host=$HOST port=5000
'''


def main(args):
    if len(args) != 2:
        sys.stderr.write("usage: %s <media file>\n" % args[0])
        sys.exit(1)

    filepath = args[1]
    
    GObject.threads_init()
    Gst.init(None)
        
    # Gst.Pipeline https://lazka.github.io/pgi-docs/Gst-1.0/classes/Pipeline.html
    pipeline = Gst.Pipeline()

    # Creates element by name
    # https://lazka.github.io/pgi-docs/Gst-1.0/classes/ElementFactory.html#Gst.ElementFactory.make
    
    # 1. src
    src = Gst.ElementFactory.make("filesrc", "mp4_file_src")
    # src.set_property("num-buffers", 50)
    src.set_property("location", filepath)
    assert src is not None
    
    # 2. qtdemux
    qtdemux = Gst.ElementFactory.make("qtdemux", "demux")
    assert qtdemux is not None
    
    # 3. h264parse
    h264parse = Gst.ElementFactory.make("h264parse")
    
    omxh264dec = Gst.ElementFactory.make("omxh264dec")
    omxh264enc = Gst.ElementFactory.make("omxh264enc")
    omxh264enc.set_property("insert-sps-pps", True)
    
    # 4. rtph264pay
    rtph264pay = Gst.ElementFactory.make("rtph264pay")
    
    # 5. sink
    sink = Gst.ElementFactory.make("udpsink")
    sink.set_property("port", 5000)
    sink.set_property("host", "192.168.31.175")
    
    # 6. link together
    pipeline.add(src, qtdemux, h264parse, omxh264dec, omxh264enc, rtph264pay, sink)
    
    # dynamically link demux when available
    def on_pad_added(element, pad):
        """Callback to link a/v sink to decoder source."""
       if pad.name == 'video_0':
           print("linking videoqueue with decoder")
           pad.link(h264parse.get_static_pad("sink"))

        # elif string.startswith('audio/'):
        #     print "linking audioqueue with decoder"
        #     pad.link(h264parse.get_static_pad("sink"))

    qtdemux.connect("pad-added", on_pad_added)

    src.link(qtdemux)
    h264parse.link(omxh264dec)
    omxh264dec.link(omxh264enc)
    omxh264enc.link(rtph264pay)
    rtph264pay.link(sink)

    # https://lazka.github.io/pgi-docs/Gst-1.0/classes/Bus.html
    bus = pipeline.get_bus()

    # allow bus to emit messages to main thread
    bus.add_signal_watch()

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    # Init GObject loop to handle Gstreamer Bus Events
    loop = GObject.MainLoop()

    # Add handler to specific signal
    # https://lazka.github.io/pgi-docs/GObject-2.0/classes/Object.html#GObject.Object.connect
    bus.connect("message", bus_call, loop)

    try:
      loop.run()
    except:
      pass
    
    # cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))