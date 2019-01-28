#!/usr/bin/env python

import rospy 
import os
import re
from threading import Lock
import jsonpickle
from gauss_commander.gauss_file_exception import GaussFileException

class TrajectoryFileHandler:
       
    def __init__(self, trajectory_dir):
        self.base_dir = trajectory_dir
        if self.base_dir.startswith('~'):
            self.base_dir = os.path.expanduser(self.base_dir)
        if not self.base_dir.endswith('/'):
            self.base_dir += '/'
        if not os.path.exists(self.base_dir): 
            print("Create trajectory dir " + str(self.base_dir))
            os.makedirs(self.base_dir)
        self.lock = Lock()

    def get_all_filenames(self):
        filenames = []
        try:
            filenames = os.listdir(self.base_dir)
        except OSError:
            pass
        r = re.compile("^trajectory_\d+$")
        # Keep only correct filenames
        return filter(r.match, filenames)

    def does_file_exist(self, filename):
        filenames = self.get_all_filenames()
        return filename in filenames

    def trajectory_id_from_filename(self, filename):
        return int(filename.replace('trajectory_', '')) 

    def filename_from_trajectory_id(self, traj_id):
        return 'trajectory_' + str(traj_id)

    def remove_trajectory(self, traj_id):
        filename = self.filename_from_trajectory_id(traj_id)
        with self.lock:
            try:
                os.remove(self.base_dir + filename)
            except OSError as e:
                raise GaussFileException("Could not remove trajectory with id " 
                        + str(traj_id) + " : " + str(e))

    def pick_new_id(self):
        filenames = self.get_all_filenames()
        max_id = 0
        for filename in filenames:
            current_id = self.trajectory_id_from_filename(filename)
            if current_id > max_id:
                max_id = current_id
        return max_id + 1
                     
    def write_trajectroy(self,traj):
        filename = self.filename_from_trajectory_id(traj.id)
        with self.lock: 
            with open(self.base_dir + filename, 'w') as f: 
                f.write(self.object_to_json(traj))
                
                
    def read_trajectory(self,trajectory_id ): 
        filename = self.filename_from_trajectory_id(trajectory_id)
        # Check if exists
        if not self.does_file_exist(filename):
            raise GaussFileException(' ' + str(trajectory_id)+ ' does not exist')
        with self.lock:
            with open(self.base_dir + filename, 'r') as f:
                try : 
                    json_str = f.read()
                    return self.json_to_object(json_str)
                except Exception as e : 
                    raise GaussFileException("Could not read trajectory with id " 
                        + str(trajectory_id)+ str(e) )
    
    def object_to_json(self, obj): 
        return jsonpickle.encode(obj)
    
    def json_to_object(self, json_str): 
        return jsonpickle.decode(json_str)
