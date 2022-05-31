from xmlrpc.client import boolean
import serial, time
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import serial.tools.list_ports as prtlst
DEBUG = True

class ModbusPull():
    def __init__(self):    
        self.msgError = ''
        self.__timerun = 0
        self.__initCom(1)
        
    def __initCom(self,timeout = 0.5):
        PORT = self.__getCOMs()
        if self.msgError == 'ok':
            self.master = modbus_rtu.RtuMaster(
                serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0)
            )
        else:self.master = None
        self.settings(timeout)
        self.settings(0.1)

    def settings(self,set_timeout):
        if self.msgError != 'ok': return
        self.master.set_timeout(set_timeout)
        #self.master.set_verbose(True)

    def __getCOMs(self):
        COMs=[]
        pts= prtlst.comports()

        for pt in pts:
            if DEBUG:print(pt)
            if 'USB' in pt[1]: #check 'USB' string in device description
                COMs.append(pt[0])
            elif 'ttyS' in pt[1]: #check 'USB' string in device description
                COMs.append(pt[0])
            elif 'COM4' in pt[1]: #check 'USB' string in device description
                COMs.append(pt[0])

        try:     
            self.msgError = 'ok'
            if DEBUG:print(COMs[0], flush=True)
            return COMs[0]
        except:

            self.msgError = 'NO COM'
            if DEBUG:print(self.msgError, flush=True)
            return 0

    def get_data(self,id,function,address,value,format = None, tries= 3):
        retries = tries
        for i in range(retries):
            self.__wait_to_next_time(timeout = 0.025)
            try:
                
                if format == None:
                    dataGet = self.master.execute(id, function, address, value)  
                else:
                    dataGet = self.master.execute(id, function, address, value,data_format = format)  
                self.__save_time_run()  
                return True, dataGet      
            except Exception:
                self.__save_time_run()
                continue
        return False, 0

    def __save_time_run(self):
        self.__timerun = time.time()

    def __wait_to_next_time(self,timeout = 0.035):
        time_switch_frame = time.time() - self.__timerun 
        if  time_switch_frame < timeout: 
            if DEBUG:print("wait send",timeout - time_switch_frame , flush=True)
            time.sleep(timeout - time_switch_frame)  

    def send_data(self,id,function,address,value,format = None,tries = 3)->boolean:
        retries = tries
        for i in range(retries):
            self.__wait_to_next_time(timeout = 0.025)
            try:
                if DEBUG:print("ID",id,"retry",i, flush=True)
                if format == None:
                    self.master.execute(id, function, address, output_value = value)
                else:
                    self.master.execute(id, function, address, output_value = value,data_format = format)
                self.stateModbus = 0
                self.__save_time_run()
                return True   
            except Exception:
                self.__save_time_run()
                continue
                
        self.stateModbus = id
        return False  
    """
    def getData(self,id,function,begin,end,):
        dataJ = {
            'sts':0,
            'dta':0
        }
        try:
            dataJ['dta'] = self.master.execute(id, function, begin, end)          
        except modbus_tk.modbus.ModbusError as e:
            dataJ['sts'] = 1
            dataJ['dta'] = 1
        except modbus_tk.modbus_rtu.ModbusInvalidResponseError as e:
            dataJ['sts'] = 2
            dataJ['dta'] = 2
        except:
            dataJ['sts'] = 3
            dataJ['dta'] = 3
        return dataJ
            
        

    def setData(self,id,function,begin,data):
        dataJ = {
            'sts':0,
            'dta':0
        }
        try:
            dataJ['dta'] = self.master.execute(id, function, begin, output_value = data)
        except modbus_tk.modbus.ModbusError as e:
            dataJ['sts'] = 1
            dataJ['dta'] = 1
        except modbus_tk.modbus_rtu.ModbusInvalidResponseError as e:
            dataJ['sts'] = 2
            dataJ['dta'] = 2
        except:
            dataJ['sts'] = 3
            dataJ['dta'] = 3
        return dataJ
    """
class controlPump(ModbusPull):
    def __init__(self):
        super().__init__()
        self.time_start_pump=0
        self.stateModbus = 0
        for i in range(192,206):
            self.set_speed_pump(i,rpm = 400.0)

    def check_finish(self, id , total_time = 0)->boolean:
        if time.time() - self.time_start_pump >total_time:
            self.stop_pump(id)
            return True
        return False

    def enable_rs485(self, id):
        self.send_data(id, function = cst.WRITE_SINGLE_COIL, address = 4100, value = 1)  

    def set_speed_pump(self, id , rpm):
        self.enable_rs485(id)
        self.send_data(id, function = cst.WRITE_MULTIPLE_REGISTERS, address = 12289, value = [rpm],format='>f')  

    def stop_pump(self, id ):
        self.enable_rs485(id)
        self.send_data(id, function = cst.WRITE_SINGLE_COIL, address = 4097, value = 0) 

    def start_pump(self, id)->boolean:
        self.enable_rs485(id)
        self.time_start_pump = time.time() 
        return self.send_data(id, function = cst.WRITE_SINGLE_COIL, address = 4097, value = 1) 

    def checkState(self,id):
        status = 1 # fail
        start_address =0
        if (id >192):
            start_address = 4100
        status,_ = self.get_data(id,cst.READ_INPUT_REGISTERS,start_address,1)
        return status

if __name__ == "__main__":
    import time
    controlPump = controlPump()
    status = True
    while(True):
        time.sleep(1)
        if status == True:
            controlPump.start_pump(193)
            status = False
        if controlPump.check_finish(193,total_time = 5):
            status = True
            time.sleep(5)
"""
#supported modbus functions
RAW = 0
READ_COILS = 1
READ_DISCRETE_INPUTS = 2
READ_HOLDING_REGISTERS = 3
READ_INPUT_REGISTERS = 4
WRITE_SINGLE_COIL = 5
WRITE_SINGLE_REGISTER = 6
READ_EXCEPTION_STATUS = 7
DIAGNOSTIC = 8
REPORT_SLAVE_ID = 17
WRITE_MULTIPLE_COILS = 15
WRITE_MULTIPLE_REGISTERS = 16
READ_FILE_RECORD = 20
READ_WRITE_MULTIPLE_REGISTERS = 23
DEVICE_INFO = 43

def main(modbusmaster):
    print(modbusmaster.getData(1,3,0,3))
    print(modbusmaster.setData(1,6,4,500)) ##WRITE_SINGLE_REGISTER
    print(modbusmaster.setData(1,16,4,[100,100,100,100,100,100,100,100])) ##WRITE_MULTIPLE_REGISTERS
if __name__ == "__main__":
    modbus = modbuspull()
    main(modbus)
"""