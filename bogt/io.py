
import rtmidi
from rtmidi import midiutil

apis = {
    rtmidi.API_MACOSX_CORE:  "OS X CoreMIDI",
    rtmidi.API_LINUX_ALSA:   "Linux ALSA",
    rtmidi.API_UNIX_JACK:    "Jack Client",
    rtmidi.API_WINDOWS_MM:   "Windows MultiMedia",
    rtmidi.API_RTMIDI_DUMMY: "RtMidi Dummy"
}


def get_available_apis():
    '''A list of (index, name) tuples of compiled MIDI APIs'''
    return [(i, apis[i]) for i in rtmidi.get_compiled_api()]


def get_input_ports(api):
    midi = rtmidi.MidiIn(api)
    return midi.get_ports()


def get_output_ports(api):
    midi = rtmidi.MidiOut(api)
    return midi.get_ports()


class Session(object):

    def __init__(self, conf):
        self.conf = conf
        self.midi_in, port_name = midiutil.open_midiport(
            port=conf['port_in'],
            type_='input',
            api=conf['api']
        )
        self.midi_in.ignore_types(sysex=False)
        self.midi_out, port_name = midiutil.open_midiport(
            port=conf['port_out'],
            type_='output',
            api=conf['api']
        )

    def query_device_info(self):
        pass
