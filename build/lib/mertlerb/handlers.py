"""
Function to parse globals() dict and class to manage communication with guis
"""
from types import ModuleType, TypeType, BuiltinFunctionType, FunctionType
from types import ClassType
from sys import getsizeof
import api
import zmq
import threading
import time
import os

_MAXCHARS = 50 # max num of chars displayed in value column of gui

# strip globals() of the following
_extras = ['In', 'Out', 'exit', 'get_ipython', 'quit'] # random keys to get rid of in globals()
_excludedtypes = [#ModuleType, TypeType, BuiltinFunctionType, FunctionType,
                  ClassType]
_excludedclasses = ['Macro', 'module', 'type', 'builtin_function_or_method',
                    'function', 'class', 'ManagedProperties']

def parse(_v): # function to parse copy of globals() dict
    # remove hidden/extra global vars, and excluded classes and types
    [_v.pop(_k, None) for _k in _v.keys() if _k[0] == '_']
    [_v.pop(_k, None) for _k in _v.keys() if _k in _extras]
    [_v.pop(_k, None) for _k in _v.keys() if type(_v[_k]) in _excludedtypes]
    [_v.pop(_k, None) for _k in _v.keys() if _v[_k].__class__.__name__ in _excludedclasses]

    # extract and stringify keys, types, sizes, values`
    _keys = [str(_k) for _k in _v.keys()]
    _types = [str(_v[_x].__class__.__name__) for _x in _keys]
    _sizes = [str(getsizeof(_v[_x]))+' bytes' for _x in _keys]
    _vals = [str(_v[_x]) for _x in _keys]
    for _ind in range(len(_vals)):
        _vals[_ind] = _vals[_ind].replace('\n', '\\n') # remove newlines
        if len(_vals[_ind]) > _MAXCHARS: # truncate
            _vals[_ind] = _vals[_ind].replace(_vals[_ind][_MAXCHARS:], '...')
        if _types[_ind] == 'ndarray': # if value is numpy array
            _types[_ind] = str(_v[_keys[_ind]].shape) + ' ndarray' # add shape info to type string

    _current = {} # format dict of dicts for outgoing json message
    for _n, _i in enumerate(_keys):
        _current[_i] = {'name':_i, 'value':_vals[_n], 'type':_types[_n], 'size': _sizes[_n]}

    if _current == {}: # if there are no variables, send semaphore to clear gui
        _current['cLeArFlAg'] = None

    return _current


class messenger: # class that handles periodic variable checking and sends to gui
    def __init__(self, _gvs):
        self._gv = _gvs # save reference to interpreter globals()
        self._lastvars = {}
        self._context = None #zmq.Context() # start TCP stuff
        self._socket = None#self._context.socket(zmq.PAIR) # socket to talk to main gui
        self._subguisocket = None#self._context.socket(zmq.PUB) # socket to talk to all subguis
        self._guiport = None#5000
        self._subguiport = None
        self._connect() # find ports to connect to
        self._loop = None
        self._subguivars = []
        self._subguiJSONmsg = {}

    def __del__(self):
        pass

    def runauto(self): # func that checks globals and sends info to gui
        _return = None
        _newvars = parse(self._gv.copy()) # get dict of latest vars
        if _newvars != self._lastvars: # if there's been a change
            self._socket.send_json(_newvars) # send dict to gui
        else: # if no change
            self._socket.send_json({}) # send empty dict
        _return = self._socket.recv_json() # wait for response
        self._send2subgui() # let ur side hoes know you still love em
        if _return: # if we got a response
            if 'KILL' in _return.keys(): # and if it was a kill flag
                api.kill() # trigger shutdown
                return
            elif 'VARREQ' in _return.keys(): # check for var data request
                self._launchsubgui(_return['VARREQ'])
        self._lastvars = _newvars # update lastVariables dict
        self._loop = threading.Timer(api._UPDATETIME, self.runauto) # reset timer
        self._loop.daemon = True # make sure timer thread shuts down with main inerpreter
        self._loop.start() # start timer

    def _connect(self):
        self._context = zmq.Context() # start TCP stuff
        self._socket = self._context.socket(zmq.PAIR) # socket to talk to main gui
        self._subguisocket = self._context.socket(zmq.PUB) # socket to talk to all subguis
        self._guiport = 5000
        _guisocketconnected = False
        _subguisocketconnected = False
        while not _guisocketconnected:
            try: # try to connect to port
                self._socket.bind("tcp://127.0.0.1:" + str(self._guiport))
                _guisocketconnected = True # if it worked, continue
            except zmq.ZMQError: # if it didn't work, go to next port
                self._guiport += 1
        self._subguiport = self._guiport + 1 # try next port for subgui
        while not _subguisocketconnected:
            try: # try to connect
                self._subguisocket.bind("tcp://127.0.0.1:" + str(self._subguiport))
                _subguisocketconnected = True # if it worked, continue
            except zmq.ZMQError: # if it didn't work, go to next port
                self._subguiport += 1

    def _launchsubgui(self, _reqvar): #launch sub gui for requested variable
        if os.name == 'posix': # launch subgui script
            os.system("python -m mertlerb.subgui {} {} &".format(self._subguiport, _reqvar))
        else: # if windows...
            os.system("start pythonw -m mertlerb.subgui {} {}".format(self._subguiport, _reqvar))
        self._subguiJSONmsg[_reqvar] = str(self._gv[_reqvar]) # add req'd var to dict of subgui vars

    def _send2subgui(self):
        for _v in self._subguiJSONmsg.keys(): # for all subgui vars
            try: # send stringified variable value
                if self._gv[_v].__class__.__name__ == 'ndarray': # special numpy array case
                    _value = str(self._gv[_v]).replace('\n  ', ' ') # replace extra newlines that numpy adds
                else: # in not numpy case
                    _value = str(self._gv[_v]) # stringify value
                self._subguiJSONmsg[_v] = _value # update var value in subgui variables dict
            except KeyError as e: # if variable name is no longer in globals() dict because it got deleted
                self._subguiJSONmsg[_v] = 'dElEtEdFlAg' # send deleted flag
        self._subguisocket.send_json(self._subguiJSONmsg) # send the message

    def destroyconnection(self): # internal shutdown
        try:
            self._loop.cancel() # stop update thread
        except AttributeError: # in case _loop hasn't been set to be a thread yet
            pass
        self._socket.send_json({'kIlLfLaG':'bye'}) # send kill flag to gui
        self._subguisocket.send_json({'kIlLfLaG':'bye'}) # send kill flag to subguis
        time.sleep(2*api._UPDATETIME) # wait for gui to receive it
        self._socket.close() # close socket
        self._subguisocket.close() # close socket
        self._context.term() # close zmq context
