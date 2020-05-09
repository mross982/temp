# from Adafruit_IO import Client, Feed, Data aio=Client("aio_LQdZ03pF22a1m9cW0RkwivXPC5Hc")
from Adafruit_IO import Client as C_ada, RequestError, Feed, Data
from twilio.rest import Client
import threading
import time
import sys
import inspect

DEVICESDIR = "/sys/bus/w1/devices/"
aio = C_ada('mross982','aio_LQdZ03pF22a1m9cW0RkwivXPC5Hc')
#aio =  MQTTClient('mross982', 'aio_LQdZ03pF22a1m9cW0RkwivXPC5Hc')


#class for holding temperature values
class Temperature():
    def __init__(self, rawData):
        self.rawData = rawData
    @property
    def C(self):
        return float(self.rawData) / 1000
    @property
    def F(self):
        return self.C * 9.0 / 5.0 + 32.0

#class for controlling the temperature sensor
class TempSensorController(threading.Thread):
    def __init__(self, sensorId, timeToSleep):
        threading.Thread.__init__(self)
       
        #persist the file location
        self.tempSensorFile = DEVICESDIR + sensorId + "/w1_slave"

        #persist properties
        self.sensorId = sensorId
        self.timeToSleep = timeToSleep

        #update the temperature
        self.updateTemp()
       
        #set to not running
        self.running = False
       
    def run(self):
        #loop until its set to stopped
        self.running = True
        while(self.running):
            #update temperature
            self.updateTemp()
            #sleep
            time.sleep(self.timeToSleep)
        self.running = False
       
    def stopController(self):
        self.running = False

    def readFile(self):
        sensorFile = open(self.tempSensorFile, "r")
        lines = sensorFile.readlines()
        sensorFile.close()
        return lines

    def updateTemp(self):
        data = self.readFile()
        #the output from the tempsensor looks like this
        #f6 01 4b 46 7f ff 0a 10 eb : crc=eb YES
        #f6 01 4b 46 7f ff 0a 10 eb t=31375
        #has a YES been returned?
        if data[0].strip()[-3:] == "YES":
            #can I find a temperature (t=)
            equals_pos = data[1].find("t=")
            if equals_pos != -1:
                tempData = data[1][equals_pos+2:]
                #update temperature
                self.temperature = Temperature(tempData)
                #update success status
                self.updateSuccess = True
            else:
                self.updateSuccess = False
        else:
            self.updateSuccess = False
       
def send_sms(msg):
    # the following line needs your Twilio Account SID and Auth Token
    if isinstance(msg, str):
        client = Client("AC1f71ca839c8a301d362a5077b615b903", "45da2cf8f6330179c36a2de62329e298")
        client.messages.create(to="+1 512-751-8734", 
                        from_="+14016859413", 
                        body=msg)
                       
                       
if __name__ == "__main__":

    #create temp sensor controller, put your controller Id here
    # look in "/sys/bus/w1/devices/" after running
    #  sudo modprobe w1-gpio
    #  sudo modprobe w1-therm
    tempcontrol = TempSensorController("28-01145efae375", 1)
    send_msg=False
    try:
        print("Starting temp sensor controller")
        #start up temp sensor controller
        tempcontrol.start()
        #loop forever, wait for Ctrl C
        while(True):
            last_cel = tempcontrol.temperature.C
            last_fer = tempcontrol.temperature.F
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

            # START HERE
            #inspect.getargspec(aiosend_data())
            try:
                feeds = aio.feeds()
                for f in feeds:
                    feed = f
                    #print('Feed: {0}'.format(f.name))
                    #tmp_sensor = aio.feeds(feed_name)
            except RequestError:
                feed = Feed(name='garage-temperature-sensor')
                tmp_sensor = aio.create_feed(feed)

            metadata = {'lat': 40.726190, 'lon': -74.005334, 'ele': -6, 'created_at': None}
            aio.send_data(feed.key, last_cel, metadata)
            #print(last_cel)

            # Managing alerts through adafruit-io. this is no longer active.
            #if last_cel > -5:
                #print("freezer out of range. sending message.")
                #msg = "Your outside freezer is at {} celcius".format(str(last_cel))
                #send_sms(msg)
            #print(last_fer)
            time.sleep(300)
    #Ctrl C
    except KeyboardInterrupt:
        print("Cancelled")
   
    #Error
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    #if it finishes or Ctrl C, shut it down
    finally:
        print("Stopping temp sensor controller")
        #stop the controller
        tempcontrol.stopController()
        #wait for the tread to finish if it hasn't already
        tempcontrol.join()
    
    #send_msg = False
    if send_msg:
        print("sending message")
        msg = "Yo, your muthafukin freezer is at {} celcius and {} farenheit. YA SHITS TOO HOTTT!!!!!".format(str(last_cel), str(last_fer))
        send_sms(msg)
    print("Done")


    
