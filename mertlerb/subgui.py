import zmq
import time
from Tkinter import *
from ttk import *
import main
import sys

if __name__ == "__main__":
    port = sys.argv[1]
    var = sys.argv[2]
    lastval = ''
    context = zmq.Context() # start TCP stuff
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, '') # set filter so it only picks up it's own stuff
    socket.connect("tcp://127.0.0.1:" + str(port))

    def checkmessenger(): # check if subgui needs to close
        global lastval
        msg = socket.recv_json() # get message from messenger
        if 'kIlLfLaG' in msg.keys(): # if received kill flag
            root.destroy() # destroy
        else:
            if msg[var] !=  lastval: # if we got new variable info
                T.delete("1.0", END) # delete current string
                T.insert(END, msg[var]) # insert new one
                lastval = msg[var] # update last value
            elif msg[var] == 'dElEtEdFlAg': # if variable was deleted
                root.destroy() # kill window
            else: # no change in variable
                pass
        root.after(int(main._UPDATETIME*1000), checkmessenger) # otherwise reset timer

    def close(): # cleanup
        root.destroy()
        socket.close() # close socket
        context.term() # close zmq context

    # GUI stuff
    # root stuff
    root = Tk()
    root.title(var)
    root.protocol("WM_DELETE_WINDOW", close)
    root.after(int(main._UPDATETIME*1000), checkmessenger)
    root.attributes('-topmost',True)
    root.lift()

    # display text
    T = Text(root, height=5, width=20, wrap="none")
    T.insert(END, '')
    T.pack(expand=1, fill=BOTH)

    root.mainloop()
