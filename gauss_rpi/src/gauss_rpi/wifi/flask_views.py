#!/usr/bin/env python

from flask import flash, request, jsonify, Response

from gauss_rpi.wifi import flask_app as app
from gauss_rpi.wifi.robot_name_handler import *
import network_manager as gauss_wifi
import json


# This id will be useful to recognize robot type (Gauss),
ID_GAUSS = 1

# default values, will be replaced with values in setup launch file
HOTSPOT_SSID = 'Gauss'
HOTSPOT_PASSWORD = 'robotics'


def set_hotspot_ssid(ssid):
    global HOTSPOT_SSID
    HOTSPOT_SSID = ssid

def set_hotspot_password(password):
    global HOTSPOT_PASSWORD
    HOTSPOT_PASSWORD = password

def standard_response(status, message):
    response = jsonify({
        'detail': message
    })
    response.status_code = status
    return response


@app.route('/')
def index():
    message = "Instructions : \n"
    message += "/addWifi : connect to a new Wi-Fi (params : [ ssid, password ])\n"
    message += "/isItTheRealGauss : todo \n"
    response = jsonify({
        'detail': message
    })
    return response

@app.route('/availableConnections', methods=['GET'])
def get_available_connections():
    connection_list = gauss_wifi.get_all_available_wifi()
    connection_list = filter(lambda c : c != HOTSPOT_SSID, connection_list)
    #print connection_list
    response = jsonify({
        'connections': connection_list
    })
    response.status_code = 200
    return response

@app.route('/registeredConnections', methods=['GET'])
def get_registered_connections():
    connection_list = gauss_wifi.get_all_registered_wifi()
    connection_list = filter(lambda c : c != HOTSPOT_SSID, connection_list)
    response = jsonify({
        'connections': connection_list
    })
    response.status_code = 200
    return response
    

@app.route('/restartWifi', methods=['POST'])
def restart_wifi():
    gauss_wifi.deactivate_current_wlan0()
    gauss_wifi.activate_current_wlan0()
    return standard_response(200, "Wifi has been restarted")

@app.route('/removeConnection', methods=['POST'])
def delete_connection():
    params = request.get_json()
    #print params
    if not params:
        return standard_response(400, "No ssid given")
    ssid = params.get('ssid', None)
    if ssid is None:
        return standard_response(400, "No ssid given")

    # Check if ssid = current ssid
    current_ssid = gauss_wifi.get_current_ssid()
    #print current_ssid
    if current_ssid == ssid:
        return standard_response(400, "Gauss is currently connected to this ssid. Please connect the robot to another ssid, or switch to 'hotspot mode', and retry")

    if gauss_wifi.delete_connection_with_ssid(ssid):
        return standard_response(200, "Connection has been removed")
    else:
        return standard_response(400, "Unable to remove this connection")


@app.route('/switchToHotspot', methods=['POST'])
def switch_to_hotspot_mode():
    if gauss_wifi.get_current_ssid() == HOTSPOT_SSID:
        return standard_response(200, "Hotspot mode already activated")
    success = gauss_wifi.hard_enable_hotspot_with_ssid(HOTSPOT_SSID, HOTSPOT_PASSWORD)
    if success:
        return standard_response(200, "Hotspot mode activated")
    return standard_response(400, "Failed to activate hotspot mode")


@app.route('/addWifi', methods=['POST'])
def add_Wifi():
    params = request.get_json()
    #print params
    if not params:
        response = "Ssid or password empty"
        resp = jsonify({
            'detail': response
        })
        resp.status_code = 400
        return resp
    ssid = params.get('ssid', None)
    password = params.get('password', None)
    name = params.get('name', '')
    
    #print ssid, password, name
    if ssid is None or password is None:
        response = "Ssid or password empty"
        resp = jsonify({
            'detail': response
        })
        resp.status_code = 400
        return resp
    
    if gauss_wifi.connect_to_wifi(ssid, password):
        write_robot_name(str(name))
    else:
        gauss_wifi.hard_enable_hotspot_with_ssid(HOTSPOT_SSID, HOTSPOT_PASSWORD)
    response = "Successfully Changed Wi-Fi"
    resp = jsonify({
        'detail': response})
    resp.status_code = 200
    return resp


@app.route('/isItTheRealGauss', methods=['GET'])
def isTheRealGauss():
    response = jsonify({'name': str(read_robot_name())})
    resp = jsonify({
        'type': ID_GAUSS,
        'name': read_robot_name()})
    resp.status_code = 200
    return resp
