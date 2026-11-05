"""Owned GUI message loop used only as the known foreground target of B's focus test."""
import ctypes
import json
from pathlib import Path
import sys
import tkinter as tk

folder=Path(sys.argv[1]);folder.mkdir(parents=True,exist_ok=True)
root=tk.Tk();root.withdraw();root.title('U02-B focus fixture');root.geometry('400x180+20+60')
tk.Label(root,text='U02-B focus fixture\nGame world continues.').pack(expand=True)
root.update_idletasks()
u=ctypes.WinDLL('user32');u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p
u.SetForegroundWindow.argtypes=[ctypes.c_void_p]
hwnd=u.GetAncestor(root.winfo_id(),2)
(folder/'window.json').write_text(json.dumps(dict(hwnd=int(hwnd))),encoding='utf-8')
last=''
def poll():
    global last
    path=folder/'command.txt'
    command=path.read_text() if path.exists() else ''
    if command!=last:
        last=command
        if command=='show':
            root.deiconify();root.update_idletasks();root.lift()
            current=u.GetAncestor(root.winfo_id(),2)
            (folder/'window.json').write_text(json.dumps(dict(hwnd=int(current),shown=True)),encoding='utf-8')
            u.SetForegroundWindow(current)
        elif command=='hide':root.withdraw()
        elif command=='close':root.destroy();return
    root.after(20,poll)
root.after(20,poll);root.mainloop()
