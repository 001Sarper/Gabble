import socket
import threading
import customtkinter
from customtkinter import *
from PIL import Image
import time
from datetime import datetime
import json



def CenterWindowToDisplay(Screen: CTk, width: int, height: int, scale_factor: float = 1.0):
    """Centers the window to the main display/monitor"""
    screen_width = Screen.winfo_screenwidth()
    screen_height = Screen.winfo_screenheight()
    x = int(((screen_width/2) - (width/2)) * scale_factor)
    y = int(((screen_height/2) - (height/1.5)) * scale_factor)
    return f"{width}x{height}+{x}+{y}"


class ToplevelWindow(customtkinter.CTkToplevel):
    def save_changes(self):
        with open("config.json", "r") as json_file:
            config = json_file.read()
        with open("config.json", "w") as json_file:
            new_config = json.loads(config)
            new_config['chat_username'] = self.chat_username.get("0.0", "end").strip()
            new_config['host'] = self.host.get("0.0", "end").strip()
            new_config['port'] = self.port.get("0.0", "end").strip()
            new_config_json = json.dumps(new_config, indent=2)
            json_file.write(new_config_json)
            print("Config Saved Successfully")
            self.destroy()


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry(CenterWindowToDisplay(self, 500, 450, self._get_window_scaling()))
        self.resizable(False, False)
        self.title("FTP Settings")

        with open("config.json", "r") as json_file:
            config1 = json_file.read()
            config2 = json.loads(config1)
            chat_username = config2['chat_username']
            host = config2['host']
            port = config2['port']

        self.title1 = CTkLabel(self, text="Socket Settings", anchor="n", font=CTkFont(size=14))
        self.title1.place(rely=0.02, relx=0.41)

        self.chat_username_label = customtkinter.CTkLabel(self, text="Chat Username", anchor="nw")
        self.chat_username_label.place(rely=0.10, relx=0.05)

        self.chat_username = CTkTextbox(master=self, corner_radius=8, height=25, width=450,  border_color="#e63505", border_width=2)
        self.chat_username.place(relx=0.05, rely=0.14)
        self.chat_username.insert("0.0", chat_username)

        self.host_label = customtkinter.CTkLabel(self, text="Server IP", anchor="nw")
        self.host_label.place(rely=0.26, relx=0.05)

        self.host = CTkTextbox(master=self, corner_radius=8, height=25, width=450, border_color="#e63505",
                                        border_width=2, scrollbar_button_color="#FFCC70")
        self.host.place(relx=0.05, rely=0.30)
        self.host.insert("0.0", host)

        self.port_label = customtkinter.CTkLabel(self, text="Server Port", anchor="nw")
        self.port_label.place(rely=0.42, relx=0.05)

        self.port = CTkTextbox(master=self, corner_radius=8, height=25, width=450, border_color="#e63505",
                                        border_width=2, scrollbar_button_color="#FFCC70")
        self.port.place(relx=0.05, rely=0.46)
        self.port.insert("0.0", port)

        save_img = Image.open("icons/save_icon.png")

        self.save_changes_btn = CTkButton(master=self, text="Save Changes", width=50, height=30, corner_radius=16, fg_color="#e63505",
                             hover_color="#b52a04", border_color="#e63505", border_width=2, image=CTkImage(dark_image=save_img, light_image=save_img), command=self.save_changes)
        self.save_changes_btn.place(relx=0.5, rely=0.85, anchor="sw")

class App(customtkinter.CTk):
    def open_toplevel(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)
            self.toplevel_window.after(50, self.toplevel_window.lift)
        else:
            self.toplevel_window.focus()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry(CenterWindowToDisplay(self, 600, 450, self._get_window_scaling()))
        self.title("FTP Chat | Made with ❤")
        self.resizable(False, False)

        switch_var = customtkinter.StringVar(value="on")

        with open("config.json", "r") as json_file:
            config1 = json_file.read()
            config2 = json.loads(config1)
            self.chat_username = config2['chat_username']
            self.host = config2['host']
            self.port = config2['port']

        def mode_event():
            if switch_var.get() == "on":
                set_appearance_mode("dark")
            elif switch_var.get() == "off":
                set_appearance_mode("light")



        switch = CTkSwitch(master=self, text="Dark Mode", progress_color="#e63505", variable=switch_var, onvalue="on",
                           offvalue="off", command=mode_event)
        switch.place(relx=0.30, rely=0.027, anchor="nw")

        settings_img = Image.open("icons/settings_icon.png")

        socket_settings_btn = CTkButton(master=self, text="FTP Settings", width=125, height=30, corner_radius=32,
                                     fg_color="#e63505",
                                     hover_color="#b52a04", border_color="#e63505", border_width=2,
                                     image=CTkImage(dark_image=settings_img, light_image=settings_img),
                                     command=self.open_toplevel)
        socket_settings_btn.place(relx=0.045, rely=0.02, anchor="nw")

        self.toplevel_window = None

        reader_font = CTkFont(family="Arial", size=13)

        self.reader = CTkTextbox(master=self, corner_radius=16, font=reader_font, height=300, width=550,
                                 border_color="#e63505", border_width=2, scrollbar_button_color="#e63505",
                                 state="disabled")
        self.reader.place(relx=0.5, rely=0.45, anchor="center")

        self.send = CTkEntry(master=self, corner_radius=16, height=50, width=550, border_color="#e63505",
                             border_width=2)
        self.send.place(relx=0.5, rely=0.9, anchor="center")
        self.send.bind("<Return>", self.write)

        self.try_connection_thread = threading.Thread(target=self.try_connection)
        self.try_connection_thread.start()

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                if message == "NICK":
                    if self.chat_username != "" or None:
                        self.client.send(self.chat_username.encode("ascii"))
                    else:
                        self.reader.insert('end', "No Username defined!\n")
                else:
                    self.reader.insert('end', message + "\n")
            except:
                print("An error occurred while receiving data.")
                self.client.close()
                break

    def try_connection(self):
        while True:
            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect((self.host, int(self.port)))
                break
            except:
                continue

    def write(self, event):
        message = f"{self.chat_username}: {self.send.get()}"
        self.client.send(message.encode("ascii"))



if __name__ == "__main__":
    app = App()
    app.mainloop()