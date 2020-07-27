# Gst Python Examples

It includes two parts: using gstreamer apis in python and writing gstreamer plugins with python.

## Install Gst Python Bindings

To use gstreamer in python codes, we need to install gstreamer python bindings. See details at [install_gstreamer_python.md](https://gist.github.com/liviaerxin/9934a5780f5d3fe5402d5986fc32d070#file-install_gstreamer_python-md).

## Examples

### Use gstreamer in python

- [construct gstreamer pipeline with parse launch](./pipeline_with_parse_launch.py)
- [construct gstreamer pipeline with factory](./pipeline_with_factory.py)
- [play media file with playbin](./helloworld.py)
- [stream media file with rtp/udp](./mp4_to_rtp.py)
- [dynamically add and remove source elements](./dynamic_src.py)
- [record sound](./record_sound.py)

### Write gstreamer plugins with python

- [sample plugin](./plugins/gst/python/gstplugin_sample.py)
- [flip video](./plugins/gst/python/gstflip.py)
- [audio plotter](./plugins/gst/python/audioplot.py)
- [object detection using tensorrt](./plugins/gst/python/gst_object_detection.py)

#### Use plugins

```sh
# ~/.local/lib/gstreamer-1.0 contains `libgstpython.cpython-36m-aarch64-linux-gnu.so`.
# $PWD/plugins/gst/ has a folder named `python` where plugins are.
export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:~/.local/lib/gstreamer-1.0/:$PWD/plugins/gst/
export GST_DEBUG=python:6 # optional
```

#### Check plugins

```sh
gst-inspect-1.0 audioplot
```

#### Remove caches

```sh
rm -rf  ~/.cache/gstreamer-1.0
```

#### Run plugins

1. sample plugin

```sh
# from fake video
GST_DEBUG=python:6 gst-launch-1.0 videotestsrc ! gstplugin_py int-prop=100 float-prop=0.2 bool-prop=True str-prop="set" ! fakesink
```

2. gaussian_blur

```sh
# from fake video
gst-launch-1.0 videotestsrc ! gaussian_blur kernel=9 sigmaX=5.0 sigmaY=5.0 ! videoconvert ! autovideosink

# from file
gst-launch-1.0 filesrc location=video.mp4 ! decodebin ! videoconvert ! \
gaussian_blur kernel=9 sigmaX = 5.0 sigmaY=5.0 ! videoconvert ! autovideosink
```

3. audioplot

```sh
SRC=/home/jetson/Videos/why_xx_xx_for_Good.mp4
HOST=192.168.31.175

# sender
# audiomixer + videocompositor
gst-launch-1.0 \
    mpegtsmux name=mux ! rtpmp2tpay \
    ! udpsink port=5000 host=$HOST \
    compositor name=videomix sink_0::zorder=1 sink_0::ypos=550 sink_1::zorder=0 ! videoconvert ! omxh264enc insert-sps-pps=true bitrate=16000000 ! h264parse ! queue ! mux. \
    audiomixer name=audiomix ! audioconvert ! audioresample ! avenc_ac3 ! queue ! mux. \
    uridecodebin uri=file://$SRC name=dec \
    dec. ! audio/x-raw ! tee name=t \
    t. ! queue ! audioconvert ! audioresample ! volume volume=10.0 ! audioplot window-duration=0.01 ! 'video/x-raw, width=1280, height=150' ! videomix.sink_0 \
    t. ! queue ! audioconvert ! audioresample ! queue ! audiomix. \
    dec. ! queue ! nvvidconv ! videoconvert ! video/x-raw ! videomix.sink_1

# videocompositor
gst-launch-1.0 \
    mpegtsmux name=mux ! rtpmp2tpay \
    ! udpsink port=5000 host=$HOST \
    compositor name=videomix sink_0::zorder=1 sink_0::ypos=550 sink_1::zorder=0 ! videoconvert ! omxh264enc insert-sps-pps=true bitrate=16000000 ! h264parse ! queue ! mux. \
    uridecodebin uri=file://$SRC name=dec \
    dec. ! queue ! audio/x-raw ! tee name=t \
    t. ! queue ! audioconvert ! audioresample ! volume volume=10.0 ! audioplot window-duration=0.01 ! 'video/x-raw, width=1280, height=150' ! videomix.sink_0 \
    t. ! queue ! audioconvert ! audioresample ! avenc_ac3 ! queue ! mux. \
    dec. ! queue ! nvvidconv ! videoconvert ! video/x-raw ! videomix.sink_1
```

```sh
# receiver, or VLC: rtp://@0.0.0.0:5000
gst-launch-1.0 -v udpsrc port=5000 caps="application/x-rtp" \
! rtpmp2tdepay ! tsparse ! tsdemux name=demux \
demux. ! queue ! decodebin ! videoconvert ! fpsdisplaysink text-overlay=false sync=false \
demux. ! queue leaky=1 ! decodebin ! audioconvert ! autoaudiosink sync=false
```

> **tips**
> the sender will not generate enough fps to play smoothly because `audioplot` consumes quite a bit of time.
