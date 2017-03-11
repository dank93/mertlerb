import handlers
import os
import atexit
import sys

global _gv, _msgr
global _UPDATETIME # period (in secs) of workspace update
_UPDATETIME = 0.25 # default is 4 times per sec

def launch(): # run with globals() as arg to launch window
    """
    Launch variable explorer window.

    Args:
        Nothing

    Returns:
        Nothing

    Raises:
        Nothing
    """
    global _gv, _msgr
    _gv = sys._getframe(1).f_locals # get dict of variables in main frame
    if '_wOrKsPaCe' in _gv.keys(): # stop if there's already an active window
        return
    if os.name != 'posix' and os.name != 'nt':  # launch gui in new process
        raise OSError('Mertlerb can only run on Posix or Windows.')
    print "MERTLERB"
    atexit.register(kill) # ensure shutdown when quitting inerpreter
    _msgr = handlers.messenger(_gv) # initialize messenger class
    if os.name == 'posix':  # launch gui in new process
        os.system("python -m mertlerb.gui " + str(_msgr._guiport) + " &")
    else: # if windows
        os.system("start pythonw -m mertlerb.gui " + str(_msgr._guiport))
    _msgr.runauto() # start messenger
    _gv['_wOrKsPaCe'] = True # put flag in global variables to stop second launch

def clear():
    """
    Delete all displayed variables.

    Args:
        Nothing

    Returns:
        Nothing

    Raises:
        Nothing
    """
    _globs = sys._getframe(1).f_locals # get all vars
    _currents = handlers.parse(_globs.copy()) # get current actively displayed variables
    for _name in _currents.keys(): # for each
        if _name != '_wOrKsPaCe' and _name != 'cLeArFlAg': # in case launch hasn't been called yet
            del _globs[_name] # clear the variable

def kill(): # cleanup
    """
    Shutdown all processes and close GUI window.

    Args:
        Nothing

    Returns:
        Nothing

    Raises:
        Nothing
    """
    global _msgr, _gv
    if '_msgr' not in globals(): # in case called before launch
        return
    if _msgr: # in case msgr already deleted
        _msgr.destroyconnection() # have messenger kill threads and gui
        del _msgr
        print "-mertlerb-"
    _msgr = None
    _gv.pop('_wOrKsPaCe', None) # remove flag variable from workspace


def refreshtime(t): # set refresh time
    """
    Set how often variable explorer window updates.

    Args:
        t: Time (in seconds) between updates.  Default is 0.25

    Returns:
        Nothing

    Raises:
        Nothing
    """
    global _UPDATETIME
    _UPDATETIME = t


def _test(): # random test function
    """Nothing special."""
    print "mErTlErB"
