import picamera
import sys
import subprocess, os
import RPi.GPIO as GPIO
import time

class Camera(object):

    def __init__(self, propeller, img_folder:str, rtmp_adress:str):

        # picamera blocks streaming, depreaceated for bash command tools
        # print('creating camera')
        # self.camera = picamera.PiCamera()

        # for picture taking
        self.propeller = propeller
        self.path = img_folder

        # for streaming
        self.null = open(os.devnull, "w")
    
    def snap(self):

        # unix time in whole seconds becomes filename
        image_name = str(int(time.time())) + ".jpg"
        subprocess.Popen(["raspistill", "-vf", "-hf", "-w", "1920", "-h", "1080", "-o", "/home/pi/project/images/{0}".format(image_name)])
        self.propeller.short_spin()

    def stream(self, controller):

        # propeller spin disabled since it mucks with button events for some reason
        #self.propeller.spin_on()
        # activate stream
        # stream = subprocess.Popen("./ustream.sh")
        print("starting cam")
        self.cam = subprocess.Popen(['raspivid', '-n', '-vf', '-hf', '-t', '0', '-w', '960', '-h', '540', '-fps', '25', '-b', '500000', '-o', '-'], stdout=subprocess.PIPE)
        print("starting stream")
        self.ffmpeg = subprocess.Popen( ['ffmpeg', '-i', '-', '-vcodec', 'copy', '-an', '-metadata', 'title=""Streaming from raspberry pi camera"', '-f', 'flv', 'rtmp://1.23526611.fme.ustream.tv/ustreamVideo/23526611/Tmh6bU2fLmjw6pYygdnn7GtV3jAMbeFw'],stdin=self.cam.stdout, stdout=self.null)
        while controller.stream_switch():
            #print("streaming")
            pass
        # stream over
        print("stream over")
        self.ffmpeg.terminate()
        self.cam.terminate()
        #self.propeller.spin_off()
        time.sleep(2)

class Propeller(object):

    def __init__(self, pin:int, spin_time:int):
        self.pin = pin
        self.spin_time = spin_time

    def short_spin(self):
        # todo: threading to put spin in background
        GPIO.output(self.pin, 1)   #Outputs digital HIGH signal (5V) on pin 3
        time.sleep(self.spin_time)
        GPIO.output(self.pin, 0)   #Outputs digital LOW signal (0V) on pin 3
        # spin shortly for picture taking

    # spinning toggle used for streaming
    def spin_on(self):
        GPIO.output(self.pin, 1)
    def spin_off(self):
        GPIO.output(self.pin, 0)

class Controller(object):

    def __init__(self, stream_pin, photo_pin):
        self.stream_pin = stream_pin
        self.photo_pin = photo_pin

    def photo_button(self):
        return GPIO.input(self.photo_pin)

    def stream_switch(self):
        return GPIO.input(self.stream_pin)

def main():
    
    # setup GPIO
    GPIO.setwarnings(False)
    # reset pins
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)

    # pins
    photo_button_pin = 22
    stream_button_pin = 16
    propeller_pin = 11

    # setup pins
    GPIO.setup(photo_button_pin, GPIO.IN)
    
    # pull down, this fixes random false positive
    GPIO.setup(stream_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(propeller_pin, GPIO.OUT)

    # misc
    # where to save pictures
    picture_folder_path = "./images/"
    # where to stream
    rtmp_address = ""
    # how long should the propeller spin when you take a picture
    spin_time = 2

    # create the objects we will use
    propeller = Propeller(propeller_pin, spin_time)
    camera = Camera(propeller, picture_folder_path, rtmp_address)
    controller = Controller(stream_button_pin, photo_button_pin)

    # concept code to not use in production

    photo_button_not_down = True
    while True:
        print("running")
        if controller.stream_switch() and photo_button_not_down:
            print("stream event detected")
            camera.stream(controller)

        elif controller.photo_button() and photo_button_not_down:
            photo_button_not_down = False
            camera.snap()
        elif not controller.photo_button() and not photo_button_not_down:
            photo_button_not_down = True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
        sys.exit(0)

