#!/usr/bin/env python

import rospy
import RPi.GPIO as GPIO

from std_msgs.msg import Empty
from std_msgs.msg import Bool

from gauss_msgs.msg import HardwareStatus
from gauss_msgs.srv import SetInt
from gauss_msgs.srv import SetLeds

LED_GPIO_R = 18
LED_GPIO_G = 24
LED_GPIO_B = 22

LED_OFF        = 0
LED_BLUE       = 1
LED_GREEN      = 2
LED_BLUE_GREEN = 3
LED_RED        = 4
LED_PURPLE     = 5
LED_RED_GREEN  = 6
LED_WHITE      = 7

LED_STATE_SHUTDOWN  = 1
LED_STATE_HOTSPOT   = 2
LED_STATE_HW_ERROR  = 3
LED_STATE_OK        = 4
LED_STATE_WAIT_HOTSPOT = 5


class LEDManager:

    def set_dxl_leds(self, color):
        leds = [0,0,0,8] # gripper LED will not be used
        if color == LED_RED:
            leds = [1,1,1,8]
        elif color == LED_GREEN:
            leds = [2,2,2,8]
        elif color == LED_BLUE:
            leds = [4,4,4,8]
        # 4 is yellow, no yellow
        elif color == LED_BLUE_GREEN:
            leds = [6,6,6,8]
        elif color == LED_PURPLE:
            leds = [5,5,5,8]
        elif color == LED_WHITE:
            leds = [7,7,7,8]
        
        try:
            rospy.wait_for_service('/gauss/set_dxl_leds', timeout=2)
        except rospy.ROSException, e:
            rospy.logwarn("Gauss ROS control LED service is not up!")
        try:
            set_dxl_leds = rospy.ServiceProxy('/gauss/set_dxl_leds', SetLeds)
            set_dxl_leds(leds)
        except rospy.ServiceException, e:
            rospy.logwarn("Could not call /gauss/set_dxl_leds service")
            

    def set_led(self, color, dxl_leds=False):
        r = GPIO.LOW
        g = GPIO.LOW
        b = GPIO.LOW

        if color & 0b100:
            r = GPIO.HIGH
        if color & 0b010:
            g = GPIO.HIGH
        if color & 0b001:
            b = GPIO.HIGH
        
        GPIO.output(LED_GPIO_R, r)
        GPIO.output(LED_GPIO_G, g)
        GPIO.output(LED_GPIO_B, b)

        if dxl_leds:
            self.set_dxl_leds(color)
            self.dxl_leds_color = color
    
    
    def set_led_from_state(self, dxl_leds=False):
        if self.state == LED_STATE_SHUTDOWN:
            self.set_led(LED_PURPLE, dxl_leds)
        elif self.state == LED_STATE_HOTSPOT:
            self.set_led(LED_BLUE, dxl_leds)
        elif self.state == LED_STATE_WAIT_HOTSPOT:
            self.set_led(LED_BLUE, dxl_leds)
        elif self.state == LED_STATE_OK:
            self.set_led(LED_GREEN, dxl_leds)
        else:
            rospy.logerr("set LED_OFF")
            self.set_led(LED_OFF, dxl_leds)

    
    def callback_hotspot_state(self, msg):
        if self.state == LED_STATE_SHUTDOWN:
            return 

        if msg.data:
            if self.state != LED_STATE_HOTSPOT:
                self.state = LED_STATE_HOTSPOT
                self.set_led_from_state(dxl_leds=True)
        elif self.state == LED_STATE_HOTSPOT:
            self.state = LED_STATE_OK
            self.set_led_from_state(dxl_leds=True)
            
    
    def callback_hardware_status(self, msg):
        if self.state == LED_STATE_HOTSPOT:
            return

        if not msg.connection_up:
            rospy.logerr("connection not up, set LED_RED")
            self.set_led(LED_RED, dxl_leds=True) # blink red
            rospy.sleep(0.05)
            self.set_led_from_state(dxl_leds=True)
        else:
            if LED_OFF == self.dxl_leds_color:
                rospy.loginfo("connection has been up, set LED_GREEN")
                self.set_led(LED_GREEN, dxl_leds=True) 
            

    def callback_set_led_state(self, req):
        state = req.value
        if state == LED_STATE_SHUTDOWN:
            self.state = LED_STATE_SHUTDOWN
            self.set_led_from_state(dxl_leds=True)
        elif state == LED_STATE_WAIT_HOTSPOT:
            self.state = LED_STATE_WAIT_HOTSPOT
            self.set_led_from_state(dxl_leds=True)
        else:
            return {'status': 400, 'message': 'Not yet implemented'}
        return {'status': 200, 'message': 'Set LED OK'}
    

    def __init__(self):
        # Set warning false, and don't cleanup LED GPIO after exit
        # So the LED will be red only after the Rpi is shutdown 
        GPIO.setwarnings(False) 
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(LED_GPIO_R, GPIO.OUT)
        GPIO.setup(LED_GPIO_G, GPIO.OUT)
        GPIO.setup(LED_GPIO_B, GPIO.OUT)

        rospy.sleep(0.1)
        self.state = LED_STATE_OK 
        self.dxl_leds_color = LED_OFF
        self.set_led_from_state(dxl_leds=True)
   
        self.set_led_state_server = rospy.Service('/gauss/rpi/set_led_state', 
                SetInt, self.callback_set_led_state)

        # Subscribe to hotspot and hardware status. Those values will override standard states
        self.hotspot_state_subscriber = rospy.Subscriber('/gauss/wifi/hotspot',
                Bool, self.callback_hotspot_state)

        self.hardware_status_subscriber = rospy.Subscriber('/gauss/hardware_status',
               HardwareStatus, self.callback_hardware_status)

        rospy.loginfo('LED manager has been started.')

