# mertlerb
MATLAB-like variable explorer for interactive Python sessions

Module that displays an interactive list of variables currently in the Python
workspace, along with their values and other useful information. Double click
on a variable for even more!

Awesome Tips!:

    Run >>launch() to begin.

    Run >>kill() to terminate the display.

    Run >>clear() to delete variables from scope. (NOTE: This only deletes
    variables that are/would be displayed in the variable explorer window, which
    excludes certain types and variable names.)

    Run >>refreshtime(t) to set refresh period to 't' seconds.

    Double-click on a variable to open up an auto-updating that displays
    its full value.

    Variable names with a leading underscore (e.g. \_var) will be ignored.

    Avoid using '>>from [module] import \*' as this may import a bunch of extra
    variables that will get displayed.

    Use >>numpy.set_printoptions(threshold=numpy.nan) to prevent breaks when
    displaying large numpy arrays (though this might slow things down a bit).

More Info:

    Types and classes in mertlerb.\_excludedclasses and mertlerb.\_excludedtypes
    are ignored.

    \*This module uses ZeroMQ.

Send comments, suggestions, and beer to Daniel Kurek at dkurek93@gmail.com.
