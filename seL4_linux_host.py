import socket
import sys

client_ip = "172.16.1.55"
client_port = 1236

class ProfilerClient:
    """
    Class encpasulating the logic to control seL4 profiler over network.
    We will also recieve samples on this client from the seL4 profiler.
    """

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.socket = None


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
        Get the mappings from pid to ELF
        """
        self.send_command("MAPPINGS")
        f.write("{\n")
        f.write("\"pd_mappings\": {\n")
        data = self.socket.recv(1024).decode()
        print(str(data))
        lines = str(data).split("\n")
        for line in lines:
            content = line.split(":")
            f.write(f"\"{content[0]}\": {content[1]},\n")
        f.write("}")
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.socket.connect((self.hostname, self.port))
        except OSError:
            sys.stderr.write(f"Can't connect to {self.hostname} on port {repr(self.port)}"
                        + " ... invalid host or port?\n")
            sys.exit(1)
        
        data = self.socket.recv(1024).decode()
        print(str(data))

    def recv(self, f):
        while True:
            # receive data stream. it won't accept data packet greater than 1024 bytes
            data = self.socket.recv(1024).decode()
            f.append(str(data))

if __name__ == "__main__":
    f = open("samples.json", "w")
    profClient = ProfilerClient(client_ip, client_port)
    profClient.connect()

    profClient.get_mappings(f)
    f.close()

    f = open("samples.json", "a")

    profClient.send_command("START")
    
    profClient.recv(f)

    f.close()

    f.append("}")