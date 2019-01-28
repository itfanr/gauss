#!/usr/bin/env python

import rospy
from gauss_commander.position.position  import Position 
from gauss_commander.gauss_file_exception import GaussFileException
from gauss_commander.position.position_file_handler import PositionFileHandler
from gauss_commander.position.position_command_type import PositionCommandType
from gauss_commander.robot_commander_exception import RobotCommanderException
from gauss_commander.parameters_validation import ParametersValidation
from gauss_commander.moveit_utils import get_forward_kinematic

from gauss_msgs.msg import Position  as PositionMessage 
from gauss_msgs.srv import GetPositionList

from gauss_msgs.srv import ManagePosition
from gauss_msgs.msg import RPY
from geometry_msgs.msg import Point
from geometry_msgs.msg import Quaternion

class PositionManager:
   
    def __init__(self, position_dir, logger):
        self.fh = PositionFileHandler(position_dir)
        self.manage_position_server = rospy.Service('/gauss/position/manage_position', ManagePosition, self.callback_manage_position)
        rospy.loginfo("service manage position created") 
        
        self.get_position_list_server = rospy.Service(
                '/gauss/position/get_position_list', GetPositionList, self.callback_get_position_list)
        rospy.loginfo("get list position created") 
        
        self.validation = rospy.get_param("/gauss/robot_command_validation")
        self.parameters_validation = ParametersValidation(self.validation)
        self.gauss_ros_logger = logger
    
    def create_position_response(self, status, message, position=None):
        position_msg = PositionMessage()
        if position != None:
            position_msg.name = position.name
            position_msg.joints = position.joints 
            position_msg.rpy = Position.RPY(position.rpy.roll, position.rpy.pitch, position.rpy.yaw)
            position_msg.point = Position.Point( position.point.x, position.point.y, position.point.z) 
            position_msg.quaternion = Position.Quaternion(position.quaternion.x, position.quaternion.y,
		 position.quaternion.z, position.quaternion.w)
        return { 'status': status, 'message': message, 'position': position_msg }
    
    def callback_manage_position(self, req):
        cmd_type = req.cmd_type
        position_name = req.position_name 
        position_msg = req.position 
	rpy = Position.RPY(position_msg.rpy.roll, position_msg.rpy.pitch,  position_msg.rpy.yaw)
        point = Position.Point(position_msg.point.x, position_msg.point.y, position_msg.point.z)
        quaternion = Position.Quaternion(position_msg.quaternion.x, position_msg.quaternion.y, position_msg.quaternion.z,
		  position_msg.quaternion.w )
        position_data = Position( name = position_msg.name,
            joints = position_msg.joints, rpy=rpy, point = point, quaternion = quaternion)     

        # GET an existing position 
        if cmd_type == PositionCommandType.GET:
            pos = self.get_position(position_name)
            if pos == None:
                return self.create_position_response(400, "No position found with name : " + str(position_name))
            return self.create_position_response(200, "Position has been found", pos)
    
        # CREATE new position    
        elif cmd_type == PositionCommandType.CREATE:
            (new_position_name, msg) = self.create_new_position(position_data)
            if new_position_name == None :
                return self.create_position_response(400, msg)
            new_position = self.get_position(new_position_name)
            if new_position == None :
                return self.create_position_response(400, "Failed to create new position")
            return self.create_position_response(200, msg , new_position)
    
        # UPDATE existing sequence
        elif cmd_type == PositionCommandType.UPDATE:
            pos = self.get_position(position_name)
            if pos == None:
                return self.create_position_response(400, "No position found with name : " + position_name)
            (success, update_msg) = self.update_position(pos, position_data)
            if not success:
                return self.create_position_response(400, update_msg)
            return self.create_position_response(200, update_msg, pos)
    
        # DELETE sequence
        elif cmd_type == PositionCommandType.DELETE:
            success = self.delete_position(position_name)
            if not success:
                return self.create_position_response(400, "Could not delete position with name : " + position_name)
            return self.create_position_response(200, "Position has been deleted")
        
        # Wrong cmd_type 
        else:
            return self.create_sequence_response(400, "Wrong command type")
    
    def delete_position(self, position_name):
        try:
            self.fh.remove_position(position_name)
        except GaussFileException as e:
            return False
        return True
    
    def update_position(self, position, position_data):
        try:
            self.parameters_validation.validate_joints(position_data.joints)
        except RobotCommanderException as e:
            rospy.logwarn("Invalid joints value when updating position : " + str(e.message)) 
            return False , "Could not update position : " + str(e.message)
        position.joints = position_data.joints
        (position.point, position.rpy, position.quaternion) = get_forward_kinematic(position.joints)                     
        try:
            self.fh.write_position(position)
        except GaussFileException as e:
            return False , "Could not update position : " + str(e)
        return True , "Position has been updated"

    def get_position(self, position_name):
        try:	
            return self.fh.read_position(position_name)
        except GaussFileException as e:
            return None

    def create_new_position(self, position) :     
        if self.fh.check_position_name(position.name) == False : 
            return None, "Failed to create new position : position " + str(position.name) + " already exists"
        try:
            self.parameters_validation.validate_joints(position.joints)
        except RobotCommanderException as e:
            rospy.logwarn("Invalid joints values when creating position : " + str(e.message))
            return None, "Failed to create new position : " + str(e.message)
        try:   
            (position.point, position.rpy, position.quaternion) = get_forward_kinematic(position.joints)    
            self.fh.write_position(position)
            return position.name, "Position has been created"
        except  GaussFileException as e:
            return None, "Failed to create new position : "+ str(e) 
    
    def callback_get_position_list(self, req = None):
        pos_list = self.get_all_positions()
        msg_list = []
        for pos in pos_list:
            position_msg = PositionMessage()
            position_msg.name = pos.name
            position_msg.joints = pos.joints 
            position_msg.rpy = Position.RPY(pos.rpy.roll, pos.rpy.pitch, pos.rpy.yaw)
            position_msg.point = Position.Point( pos.point.x, pos.point.y, pos.point.z) 
            position_msg.quaternion = Position.Quaternion(pos.quaternion.x, pos.quaternion.y,
		 pos.quaternion.z, pos.quaternion.w)
            msg_list.append(position_msg)
        return { 'positions': msg_list }

    def get_all_positions(self):
        filenames = self.fh.get_all_filenames()
        position_list = []
        for f in filenames:
            try:
                position_name = self.fh.position_name_from_filename(f)
                pos = self.get_position(position_name)
                if pos != None:
                    position_list.append(pos)
            except GaussFileException as e:
                pass
        return position_list


if __name__ == '__main__':
    pass

    


