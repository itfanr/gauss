#!/usr/bin/env python

import rospy

from gauss_msgs.srv import PingDxlTool
from gauss_msgs.srv import OpenGripper
from gauss_msgs.srv import CloseGripper
from gauss_msgs.srv import SetDigitalIO


class ToolRosCommandInterface:

    def __init__(self):
        rospy.wait_for_service('gauss/tools/ping_and_set_dxl_tool')
        rospy.wait_for_service('gauss/tools/open_gripper')
        rospy.wait_for_service('gauss/tools/close_gripper')

        self.service_ping_dxl_tool = rospy.ServiceProxy('gauss/tools/ping_and_set_dxl_tool', PingDxlTool)
        
        self.service_open_gripper = rospy.ServiceProxy('gauss/tools/open_gripper', OpenGripper)
        self.service_close_gripper = rospy.ServiceProxy('gauss/tools/close_gripper', CloseGripper)
        
        self.service_setup_digital_output_tool = rospy.ServiceProxy('gauss/rpi/set_digital_io_mode', SetDigitalIO)
        self.service_activate_digital_output_tool = rospy.ServiceProxy('gauss/rpi/set_digital_io_state', SetDigitalIO)

        rospy.loginfo("Interface between Tools Controller and Ros Control has been started.")

    def ping_dxl_tool(self, tool_id, tool_name):
        try:
            if tool_id == 0:
                tool_name = "No Dxl Tool"
            resp = self.service_ping_dxl_tool(tool_id, tool_name)
            return resp.state
        except rospy.ServiceException, e:
            return ROS_COMMUNICATION_PROBLEM

    def open_gripper(self, gripper_id, open_position, open_speed, open_hold_torque):
        try:
            resp = self.service_open_gripper(gripper_id, open_position, open_speed, open_hold_torque)
            return resp.state
        except rospy.ServiceException, e:
            return ROS_COMMUNICATION_PROBLEM
    
    def close_gripper(self, gripper_id, close_position, close_speed, close_hold_torque, close_max_torque):
        try:
            resp = self.service_close_gripper(gripper_id, close_position, close_speed, close_hold_torque, close_max_torque)
            return resp.state
        except rospy.ServiceException, e:
            return ROS_COMMUNICATION_PROBLEM

    def digital_output_tool_setup(self, gpio_pin):
        try:
            rospy.wait_for_service('gauss/rpi/set_digital_io_mode', 2)
        except rospy.ROSException:
            return 400, "Digital IO panel service is not connected"
        try:
            resp = self.service_setup_digital_output_tool(gpio_pin, 0) # set output
            return resp.status, resp.message
        except rospy.ServiceException, e:
            return 400, "Digital IO panel service failed"

    def digital_output_tool_activate(self, gpio_pin, activate):
        try:
            rospy.wait_for_service('gauss/rpi/set_digital_io_state', 2)
        except rospy.ROSException:
            return 400, "Digital IO panel service is not connected"
        try:
            resp = self.service_activate_digital_output_tool(gpio_pin, activate)
            return resp.status, resp.message
        except rospy.ServiceException, e:
            return 400, "Digital IO panel service failed"

