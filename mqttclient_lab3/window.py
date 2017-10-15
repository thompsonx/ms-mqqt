import Tkinter as tk
import sys
from distutils.command.clean import clean

import paho.mqtt.client as mqtt


class Window(tk.Frame):

    def _setup_client(self, anonymous=True):
        def on_message(_client, obj, msg):
            _msg = "%s: %s" % (msg.topic, msg.payload)
            if "mschat/status/" in msg.topic:
                tokens = msg.topic.split("/")
                usr = tokens[len(tokens) - 1]
                if "online" in msg.payload:
                    self.users[usr] = "online"
                    if self.usr_msg_queue.has_key(usr):
                        for t, m in self.usr_msg_queue[usr]:
                            self._send_msg(t, m)
                if "offline" in msg.payload:
                    self.users[usr] = "offline"
            self.list.insert(0, _msg)

        def on_connect(_client, obj, flags, rc):
            self.is_connected = True
            self.client.subscribe("/mschat/#", 0)
            for topic, msg in self.msg_queue:
                _client.publish(topic, msg)
            self.list.insert(0, "INFO: CONNECTED")

        def on_disconnect(_client, userdata, rc):
            self.is_connected = False
            if rc != 0:
                self.list.insert(0, "INFO: CONNECTION LOST.")
                for usr in self.users.keys():
                    self.users[usr] = "offline"
                    self.list.insert(0, "/mschat/status/%s: offline" % (usr))

        self.isAnon = anonymous
        if anonymous:
            self.client = mqtt.Client()
            self.channel = "/mschat/all/anon"
        else:
            self.client = mqtt.Client(client_id=self.client_id)
            self.client.username_pw_set("mobilni", "Systemy")
            self.channel = "/mschat/all/" + self.client_id

            def on_connect2(_client, obj, flags, rc):
                _client.publish("/mschat/status/" + self.client_id, "online", retain=True)
                on_connect(_client, obj, flags, rc)

            self.client.on_connect = on_connect2
            self.client.will_set("/mschat/status/" + self.client_id, "offline", retain=True)

        self.client.on_message = on_message
        self.client.on_disconnect = on_disconnect

        self.client.reconnect_delay_set(min_delay=1, max_delay=1)

        self.client.connect(host=self.srvaddr.get(), port=int(self.portentry.get()), keepalive=3)

        self.client.loop_start()

    def _send_msg(self, topic, msg):
        if "mschat/user/" in topic:
            tokens = topic.split("/")
            usr = tokens[len(tokens) - 2]
            if self.users.has_key(usr):
                if self.users[usr] == "offline":
                    if self.usr_msg_queue.has_key(usr):
                        self.usr_msg_queue[usr].append((topic, msg))
                    else:
                        self.usr_msg_queue[usr] = [(topic, msg)]
                    self.list.insert(0, "INFO: User %s is offline. Message saved to queue." % usr)
                else:
                    self.client.publish(topic, msg)
            else:
                self.list.insert(0, "INFO: User %s does not exist." % usr)
        else:
            if self.is_connected:
                self.client.publish(topic, msg)
            else:
                self.list.insert(0, "LOCAL: %s: %s" % (topic, msg))
                self.msg_queue.append((topic, msg))

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)

        self.client_id = "my_nick"
        self.client = None
        self.is_connected = False
        self.users = {}
        self.usr_msg_queue = {}
        self.msg_queue = []

        self.pack(fill=tk.BOTH, expand=1)
        self._create_login()

    def _create_login(self):
        self.authframe = tk.Frame(self)

        connectionFrame = tk.Frame(self.authframe)
        srvlbl = tk.Label(connectionFrame, text="Server:")
        srvlbl.pack(side=tk.LEFT)
        self.srvaddr = tk.Entry(connectionFrame)
        self.srvaddr.insert(0, "pcfeib425t.vsb.cz")
        self.srvaddr.pack(side=tk.LEFT, expand=1, fill=tk.X)
        portlbl = tk.Label(connectionFrame, text="Port:")
        portlbl.pack(side=tk.LEFT)
        self.portentry = tk.Entry(connectionFrame)
        self.portentry.insert(0, "1883")
        self.portentry.pack(side = tk.LEFT, expand = 1, fill = tk.X)
        connectionFrame.pack(side=tk.TOP)

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
                    self.client.publish("/mschat/status/" + self.client_id, "offline", retain=True)
                self.client.disconnect()
            sys.exit()

        self.disconnect = tk.Button(self.authframe,
                            text="Disconnect",
                            command = disconnect)
        self.disconnect.pack(side=tk.TOP)
        self.disconnect.config(state="disabled")

        self.authframe.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

    def _create_widgets(self):
        self.list = tk.Listbox(self)
        self.list.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

        self.msgframe = tk.Frame(self)

        self.msgbox = tk.Entry(self.msgframe)
        self.msgbox.pack(side=tk.LEFT, expand=1, fill=tk.X)

        def sendmsg():
            msg = self.msgbox.get()
            self._send_msg(self.channel,
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
            self._send_msg("/mschat/user/" + pmtarget.get() + "/" + self.client_id,
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