#!/usr/bin/env python

import rospy 
import tf 
from gauss_commander.position.position import Position 

from moveit_msgs.msg import RobotState
from moveit_msgs.srv import GetPositionFK
from std_msgs.msg import Header


def get_forward_kinematic(joints): 

    try:
	  rospy.wait_for_service('compute_fk',2)
    except (rospy.ServiceException, rospy.ROSException), e:
          rospy.logerr("Service call failed:",e)
          return None 
    try:
	  moveit_fk = rospy.ServiceProxy('compute_fk', GetPositionFK)
	  fk_link= ['base_link','link6']
    	  joint_names = ['joint1','joint2','joint3','joint4','joint5','joint6']
    	  header = Header(0,rospy.Time.now(),"/base_link")
    	  rs = RobotState()
          rs.joint_state.name = joint_names
          rs.joint_state.position = joints
          response = moveit_fk(header, fk_link, rs)
    except rospy.ServiceException,e:
          rospy.logerr("Service call failed:",e)
	  return(None)

    quaternion=[response.pose_stamped[1].pose.orientation.x, response.pose_stamped[1].pose.orientation.y, 
	response.pose_stamped[1].pose.orientation.z, response.pose_stamped[1].pose.orientation.w]
    rpy = get_rpy_from_quaternion(quaternion)
    quaternion = Position.Quaternion(round(quaternion[0],3), round(quaternion[1],3), round(quaternion[2],3),
	round(quaternion[3],3))
    point = Position.Point(round(response.pose_stamped[1].pose.position.x,3), round(response.pose_stamped[1].pose.position.y,3),
	 round(response.pose_stamped[1].pose.position.z,3))
    rpy=Position.RPY(round(rpy[0],3),round(rpy[1],3),round(rpy[2],3))
    rospy.loginfo("kinematic forward has been calculated ") 
    return(point, rpy, quaternion)

def get_rpy_from_quaternion(rot): 
    PI = 3.14159
    euler = tf.transformations.euler_from_quaternion(rot)
    rpy=[0,0,0]
    rpy[0] = euler[1] * (-1.0)
    rpy[1] = euler[0] - PI/2.0
    rpy[2] = euler[2] - PI/2.0
                                                               
     # force angle between -PI/PI
    for i, angle in enumerate(rpy):
        if angle > PI:
            rpy[i] = angle % PI
        elif angle < -PI:
            rpy[i] = angle % -PI 
    return rpy

if __name__ == '__main__':
    pass 

