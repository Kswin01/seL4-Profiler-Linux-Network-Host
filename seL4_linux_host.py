import socket
import sys
import threading
import os

client_ip = "172.16.1.64"
client_port = 1236

stop_recv = 0

class ProfilerClient:
    """
    Class encpasulating the logic to control seL4 profiler over network.
    We 
    will also recieve samples on this client from the seL4 profiler.
    """

    def __init__(self, port):
        self.hostname = None
        self.port = port
        self.socket = None
        self.recv_thread = None
        self.f = None

    def set_ip(self, ip):
        """
        Set the IP address of the profiler client

        Params:
            ip: IP address we wish to connect to
        """
        self.hostname = ip

    def send_command(self, cmd):
        """
        Send a command to the client over telnet.

        Params:
            cmd: Command to send
        """
        print("[send_command] : " + cmd)
        self.socket.send((cmd + "\n").encode('utf-8'))

    def get_mappings(self, f):
        """
        Get the mappings from pid to ELF names
        """
        self.send_command("MAPPINGS")
        f.write("{\n")
        f.write("\"pd_mappings\": {\n")
        data = self.socket.recv(4096).decode()
        print(str(data))
        lines = str(data).split("\n")
        for line in lines:
            content = line.split(":")
            f.write(f"\"{content[0]}\": {content[1]},\n")
        f.write("}")

    def connect(self):
        #  Check if the user has set an ip address
        if self.hostname is None:
            print("Please set an IP address by typing: IP <ip_addr>")
            return 1

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.socket.connect((self.hostname, self.port))
            return 0
        except OSError:
            sys.stderr.write(f"Can't connect to {self.hostname} on port {repr(self.port)}"
                        + " ... invalid host or port?\n")
            sys.exit(1)
        
        
        data = self.socket.recv(1024).decode()
        print(str(data))


    def recv_samples_thread(self):
        while True:
            # receive data stream. it won't accept data packet greater than 1024 bytes
            # global stop_recv
            try:
                data = self.socket.recv(1024).decode()
                self.f.write(str(data))
            except socket.error:
                global stop_recv
                if stop_recv:
                    break
                else:
                    print("No data on socket")
                    # Dummy command to refresh socket
                    self.send_command("REFRESH")

    def recv_samples(self, f):
        # Start the samples section of the json
        self.socket.settimeout(2)
        global stop_recv
        stop_recv = 0
        self.recv_thread = threading.Thread(target=self.recv_samples_thread, args=())
        self.recv_thread.daemon = True
        self.f = open("samples.json", "a")
        self.recv_thread.start()

    def stop_samples(self):
        global stop_recv
        stop_recv = 1
        # time.sleep(10)
        self.recv_thread.join()
        self.f.close()


if __name__ == "__main__":
    # Intially, we want to create client object
    profClient = ProfilerClient(client_port)
    print("seL4 Profiler Network Client. Please enter command:")

    f = None

    # Create the recv thread. Start on START command, exit on STOP command.

    # Sit in a loop and wait for user commands
    while True:
        user_input = input("> ").upper()
        if user_input == "CONNECT":
            conn_ret = profClient.connect()
            if conn_ret == 0:
                f = open("samples.json", "w")
                profClient.get_mappings(f)
                f.write(",\n\"samples\": [\n")
                f.close()

        elif user_input == "START":
            f = open("samples.json", "a")
            profClient.send_command("START")
            # TODO: Start this in a seperate thread
            # recvThread = threading.Thread(target=profClient.recv_samples, args=(f))

            profClient.recv_samples(f)
            # recvThread.start()

        elif user_input == "STOP":
            # Stop the recv thread and close file descriptor
            profClient.send_command("STOP")
            profClient.stop_samples()

        elif user_input == "EXIT":
            profClient.send_command("STOP")   
            profClient.stop_samples()
            f = open("samples.json", "a")
            f.write("]\n}\n")
            f.close()
            os._exit(1)

        elif user_input.startswith("IP"):
            ip_arg = user_input.split(" ")
            if len(ip_arg) != 2:
                print("ERROR: Please supply IP address as argument")
            else:
                print(f"Setting IP address to {ip_arg[1]}")
                profClient.set_ip(ip_arg[1])
        
        else: 
            print("These are the following valid commands (case-agnostic):\n")
            print("\t1. \"CONNECT\" - This will attempt to connect to the supplied IP address and port. Connect will add the ")
            print("\t2. \"START\" - This will command the seL4 profiler to start measurements and construct samples.json file.")
            print("\t3. \"STOP\" - This will command the seL4 profiler to stop measurements.")
            print("\t4. \"EXIT\" - This will command the seL4 profiler to stop measurements, close the json file and exit this program")







