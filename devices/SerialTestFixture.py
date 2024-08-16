import serial
import serial.tools.list_ports


def get_ports():
    ports = serial.tools.list_ports.comports()
    com_list = []
    for p in ports:
        com_list.append(p.device)
    return com_list


###############################################################################
## SerialTestFixture class to communicate with Serial ports
###############################################################################
class SerialTestFixture(object):
    ###############################################################################
    ## @brief Initializer for the class.
    ## @param port        Port being used / where data is being sent from
    ## @param baud_rate
    ## @param parity
    ## @param data_bits
    ## @param stop_bits
    ###############################################################################

    def __init__(self, port='', baud_rate=None, data_bits=None, parity='', stop_bits=None, timeout=1) -> None:
        super().__init__()
        self.__port = port
        self.__baud_rate = baud_rate
        self.__parity = parity
        self.__data_bits = data_bits
        self.__stop_bits = stop_bits
        self.__timeout = timeout
        self.__serial_conn = serial.Serial()

    def setup(self):
        self.__serial_conn = serial.Serial(
            port=self.__port,
            baudrate=self.__baud_rate,
            parity=self.__parity,
            bytesize=self.__data_bits,
            stopbits=self.__stop_bits,
            timeout=self.__timeout
        )
        print(self.__serial_conn)
        return self.__serial_conn

    def is_port_open(self):
        try:
            if self.__serial_conn:
                return self.__serial_conn.is_open
            else:
                print('Port is Closed')
                return False
        except Exception as ex:
            print("An error occurred while trying to setup UTF")
            print(ex)
            raise ex

    def close(self):
        try:
            if self.__serial_conn:
                self.__serial_conn.close()
        except Exception as ex:
            print("An error occurred while trying to close UTF")
            print(ex)
            raise ex

    def write(self, data):
        try:
            if self.__serial_conn:
                self.__serial_conn.write(data.encode('utf-8'))
                return f"Data {data} has been written"
            else:
                return f"Data cannot be written, port is CLOSED"
        except Exception as ex:
            print("An error occurred while trying to write to UTF")
            print(ex)
            raise ex

    def read(self, data):
        try:
            if self.__serial_conn:
                print(f"Reading Data")
                return self.__serial_conn.read(data)
            else:
                return f"Data cannot be read, port is CLOSED"
        except Exception as ex:
            print("An error occurred while trying to read from UTF")
            print(ex)
            raise ex