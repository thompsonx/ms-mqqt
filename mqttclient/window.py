import Tkinter as tk
import sys

import paho.mqtt.client as mqtt


class Window(tk.Frame):

    def _create_widgets(self):
        self.list = tk.Listbox(self)
        self.list.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

        self.msgframe = tk.Frame(self)

        self.msgbox = tk.Entry(self.msgframe)
        self.msgbox.pack(side=tk.LEFT, expand=1, fill=tk.X)

        def sendmsg():
            msg = self.msgbox.get()
            self.client.publish(self.channel,
                                msg)

        self.sendbtn = tk.Button(self.msgframe,
                                 text="Send",
                                 command = sendmsg)
        self.sendbtn.pack(side=tk.LEFT)

        self.msgframe.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

    def _create_PM(self):
        self.pmframe = tk.Frame(self)

        pmlabel = tk.Label(self.pmframe,
                           text="Private messages")
        pmlabel.pack(side=tk.TOP)

        pmtargetframe = tk.Frame(self.pmframe)

        pmtargetlabel = tk.Label(pmtargetframe,
                                 text="Target:")
        pmtargetlabel.pack(side=tk.LEFT)
        pmtarget = tk.Entry(pmtargetframe)
        pmtarget.pack(side=tk.LEFT, expand=1, fill=tk.X)

        pmtargetframe.pack(side=tk.TOP)

        pmmsgframe = tk.Frame(self.pmframe)
        pmmsg = tk.Entry(pmmsgframe)
        pmmsg.pack(side=tk.LEFT, expand=1, fill=tk.X)

        def sendmsg():
            msg = pmmsg.get()
            self.client.publish("/mschat/user/" + pmtarget.get() + "/" + self.client_id,
                                msg)

        pmmsgsend = tk.Button(pmmsgframe,
                                 text="Send",
                                 command=sendmsg)
        pmmsgsend.pack(side=tk.LEFT)

        pmmsgframe.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

        # pmlist = tk.Listbox(self.pmframe)
        # pmlist.pack(side=tk.TOP, expand=1, fill=tk.BOTH)
        #
        # pmclient = mqtt.Client(client_id=self.client_id)
        # pmclient.username_pw_set("mobilni", "Systemy")
        # pmclient.connect(host="pcfeib425t.vsb.cz", port=1883)

        self.pmframe.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

    def _setup_client(self, anonymous=True):
        def on_message(_client, obj, msg):
            msg = "%s: %s" % (msg.topic, msg.payload)
            self.list.insert(0, msg)
        self.client = None
        self.isAnon = anonymous
        if anonymous:
            self.client = mqtt.Client()
            self.channel = "/mschat/all/anon"
        else:
            self.client = mqtt.Client(client_id=self.client_id)
            self.client.username_pw_set("mobilni", "Systemy")
            self.channel = "/mschat/all/" + self.client_id
            def on_connect(_client, obj, flags, rc):
                _client.publish("/mschat/all/" + self.client_id,
                                self.client_id + " is online", retain=True)
            self.client.on_connect = on_connect
            self.client.will_set("/mschat/all/" + self.client_id,
                                self.client_id + " lost connection", retain=True)

        self.client.on_message = on_message

        self.client.connect(host="pcfeib425t.vsb.cz", port=1883)
        self.client.subscribe("/mschat/#", 0)

        self.client.loop_start()

    def _create_login(self):
        self.authframe = tk.Frame(self)

        authorizedframe = tk.Frame(self.authframe)
        namebox = tk.Entry(authorizedframe)
        namebox.pack(side=tk.LEFT, expand=1, fill=tk.X)

        def connect():
            self._create_widgets()
            self.login.config(state="disabled")
            self.anonym.config(state="disabled")
            self.disconnect.config(state="normal")

        def authorized():
            connect()
            self.client_id = namebox.get()
            self._setup_client(False)
            self._create_PM()
        self.login = tk.Button(authorizedframe,
                          text="Authorized connection",
                          command = authorized)
        self.login.pack(side=tk.LEFT)

        authorizedframe.pack(side=tk.TOP)

        def anonymous():
            connect()
            self._setup_client()
        self.anonym = tk.Button(self.authframe,
                            text="Anonymous connection",
                            command = anonymous)
        self.anonym.pack(side=tk.TOP)

        def disconnect():
            if self.client is not None:
                self.client.loop_stop()
                if not self.isAnon:
                    self.client.publish("/mschat/all/" + self.client_id,
                                        self.client_id + " is offline", retain=True)
                self.client.disconnect()
            sys.exit()

        self.disconnect = tk.Button(self.authframe,
                            text="Disconnect",
                            command = disconnect)
        self.disconnect.pack(side=tk.TOP)
        self.disconnect.config(state="disabled")

        self.authframe.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)

        self.client_id = "my_nick"

        self.pack(fill=tk.BOTH, expand=1)
        self._create_login()