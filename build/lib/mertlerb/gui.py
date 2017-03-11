from Tkinter import *
from ttk import *
import zmq
import time
import api
import sys

if __name__ == "__main__":
    port = sys.argv[1]
    context = zmq.Context() # make sockets, etc.
    socket = context.socket(zmq.PAIR)
    socket.connect("tcp://127.0.0.1:" + str(port))

    varrequest = False
    def updateGUI(): # callback to update display
        global varrequest
        msg = socket.recv_json() # get info from messenger
        if varrequest: # if double click triggered, sent request for variable
            socket.send_json({'VARREQ':tree.item(varrequest)['text']})
        else: # otherwise send normal 'OK' message
            socket.send_json({'OK':None}) # send reponse
        varrequest = False # reset varrequest flag
        if 'kIlLfLaG' in msg.keys(): # if received kill flag
            root.destroy() # close gui
            return
        elif 'cLeArFlAg' in msg.keys(): # if we got a clear all vars flag
            try:
                display({}) # display nothing
            except TclError:
                pass
        elif msg: # if no flags but still has content
            try:
                display(msg) # display latest batch of variables
            except TclError:
                pass
        else: # do nothing if recieved empty dict
            pass
        root.after(int(api._UPDATETIME*1000), updateGUI) # do again after _UPDATETIME secs

    def display(m): # displays vars
        k = [str(kk) for kk in m.keys()]
        k.sort(key=str.lower) # alphabetize new vars
        for row in tree.get_children():
            tree.delete(row) # delete current displayed vars
        for num, i in enumerate(k): # make new items and insert into gui
            n = m[i]['name']
            v = (m[i]['value'], m[i]['type'])#, m[i]['size'])
            tree.insert("" , num, text=n, values=v)

    lastdoubleclick = time.time()
    def OnDoubleClick(event): # double click callback - request full selected var data to be sent
        # timer is because function executes twice first the time user double
        # clicks after focusing on a different window
        global lastdoubleclick, varrequest
        if time.time() - lastdoubleclick > 0.3:
            item = tree.selection() # get selected item id
            varrequest = item # raise flag to stop gui from sending next 'OKAY' response, to prevent the buffer from filling
            lastdoubleclick = time.time() # reset timer

    def close(): # gui close callback
        root.destroy() # close window
        socket.send_json({'KILL':None}) # initiate full shutdown
        time.sleep(2*api._UPDATETIME) # wait a bit
        socket.close() # close sockets
        context.term()

    # GUI stuff
    # root stuff
    root = Tk()
    root.title('Workspace')
    root.protocol("WM_DELETE_WINDOW", close)
    root.after(int(api._UPDATETIME*1000), updateGUI)
    root.lift()
    root.attributes('-topmost',True)

    # make tree
    tree = Treeview(root)
    tree["columns"]=("value", "type")#, "size")
    tree.column("#0", width=70, anchor='center')
    tree.column("value", width=70, anchor='center')
    tree.column("type", width=70, anchor='center')
    # tree.column("size", width=70, anchor='center')
    tree.heading("#0", text="Name")
    tree.heading("value", text="Value")
    tree.heading("type", text="Type")
    # tree.heading("size", text="Size")
    tree.bind("<Double-1>", OnDoubleClick)
    tree.pack(expand=1, fill=BOTH)

    # run gui
    root.mainloop()
