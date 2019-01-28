#!/usr/bin/env python

import rospy
import actionlib
import threading

# import Gauss api
from gauss_python_api.gauss_api import *

# Action msgs
from gauss_msgs.msg import SequenceAction
from gauss_msgs.msg import SequenceGoal
from gauss_msgs.msg import SequenceResult

from gauss_msgs.msg import Sequence as SequenceMessage
from gauss_commander.command_status import CommandStatus

from sequence_manager import SequenceManager
from gauss_user_interface.sequences.sequence_code_executor import SequenceCodeExecutor
from gauss_user_interface.sequences.sequence_action_type import SequenceActionType


class SequenceActionServer:

    def __init__(self, sequence_manager, logger):
        self.gauss_ros_logger = logger

        self.server = actionlib.ActionServer('gauss/sequences/execute',
                SequenceAction, self.on_goal, self.on_cancel, auto_start=False)

        self.seq_code_executor = SequenceCodeExecutor()

        self.current_goal_handle = None

        self.seq_manager = sequence_manager

    def start(self):
        self.server.start()
        rospy.loginfo("Action Server started (Sequence Action)")

    def create_result(self, status, message):
        result = SequenceResult()
        result.status = status
        result.message = message
        return result
    
    def on_goal(self, goal_handle):
        rospy.loginfo("Sequence action server : Received goal. Check if exists")
        # print goal_handle.__dict__

        # check if still have a goal -> set_rejected() 
        if self.current_goal_handle is not None:
            result = self.create_result(CommandStatus.GOAL_STILL_ACTIVE, "Current command still active. Cancel it if you want to execute a new one")
            goal_handle.set_rejected(result)
            return
      
        # set accepted
        self.current_goal_handle = goal_handle
        self.current_goal_handle.set_accepted()
        rospy.loginfo("Sequence server : Goal has been accepted")

        # Launch execution in a new thread
        w = threading.Thread(name="worker", target=self.execute_action)
        w.start()
        rospy.loginfo("Sequence server : Executing thread")
    
    def on_cancel(self, goal_handle):
        rospy.loginfo("Received cancel command")

        if goal_handle == self.current_goal_handle:
            self.cancel_current_command()
        else:
            rospy.loginfo("No current goal, nothing to do")

    def cancel_current_command(self):
        self.seq_code_executor.cancel_execution()
    
    def execute_action(self):
        cmd_type = self.current_goal_handle.goal.goal.cmd_type
        sequence_id = self.current_goal_handle.goal.goal.sequence_id
        sequence = self.current_goal_handle.goal.goal.sequence

        self.gauss_ros_logger.publish_log_status("INFO", "SequenceActionServer execute_action begin")

        if cmd_type == SequenceActionType.EXECUTE_FROM_ID:
            # 1. Retrieve sequence from id
            sequence = self.seq_manager.get_sequence_from_id(sequence_id)
            if sequence == None:
                result = self.create_result(CommandStatus.SEQUENCE_FAILED, "No sequence found with id " + str(sequence_id))
                self.current_goal_handle.set_aborted(result)
                self.current_goal_handle = None
                self.gauss_ros_logger.publish_log_status("ERROR", "No sequence found with id")
                return
        elif cmd_type == SequenceActionType.EXECUTE_FROM_XML:
            pass
        else:
            result = self.create_result(CommandStatus.SEQUENCE_FAILED, "Wrong command type for Sequence Action Server")
            self.current_goal_handle.set_aborted(result)
            self.current_goal_handle = None
            self.gauss_ros_logger.publish_log_status("ERROR", "Wrong command type for Sequence Action Server")
            return

        # 2. Generate Python code from xml
        rospy.loginfo("Generate Python code from Blockly xml")
        self.gauss_ros_logger.publish_log_status("INFO", "Generate Python code from Blockly xml")

        response = self.seq_manager.get_python_code_from_xml(sequence.blockly_xml)
        if response['status'] != 200:
            result = self.create_result(CommandStatus.SEQUENCE_FAILED, str(response['message']))
            self.current_goal_handle.set_aborted(result)
            self.current_goal_handle = None
            self.gauss_ros_logger.publish_log_status("ERROR", result.message)
            return
        
        code = response['code']
        rospy.loginfo("Generated code :")
        rospy.loginfo(code)
      
        # 3. Save as last executed command (id : 0)
        # - Only sequences that are not previously stored
        if cmd_type != SequenceActionType.EXECUTE_FROM_ID:
            sequence.python_code = code
            self.seq_manager.save_last_executed_sequence(sequence)
            self.gauss_ros_logger.publish_log_status("INFO", "Save as last executed command")

        # 4. Execute code
        exec_result = self.seq_code_executor.execute_generated_code(code)
       
        # 5. Return exec result
        if exec_result['status'] == 300:
            result = self.create_result(CommandStatus.STOPPED, exec_result['message'])
            self.current_goal_handle.set_canceled(result)
            self.gauss_ros_logger.publish_log_status("ERROR", result.message)
        elif exec_result['status'] == 200:
            result = self.create_result(CommandStatus.SUCCESS, exec_result['message'])
            self.current_goal_handle.set_succeeded(result)
            self.gauss_ros_logger.publish_log_status("INFO", result.message)

        else:
            result = self.create_result(CommandStatus.SEQUENCE_FAILED, exec_result['message'])
            self.current_goal_handle.set_aborted(result)
            self.gauss_ros_logger.publish_log_status("ERROR", result.message)

        self.current_goal_handle = None

if __name__ == '__main__':
    #rospy.init_node('sequence_action_server')
    #s = SequenceManager('/home/edouard/sequences_gauss')
    #rospy.on_shutdown(s.shutdown)
    #seq_action = SequenceActionServer(s)
    #seq_action.start()
    #rospy.spin()
    pass
