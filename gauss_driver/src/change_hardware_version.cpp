#include "gauss_driver/change_hardware_version.h"

int change_hardware_version_and_reboot(int old_version, int new_version)
{
#ifdef __arm__
    
    std::ostringstream text;
    
    // get launch file path
    std::string folder_path = ros::package::getPath("gauss_bringup");
    std::string file_path = folder_path + "/launch/gauss_base.launch";

    std::ifstream in_file(file_path.c_str());

    // read launch file
    text << in_file.rdbuf();
    std::string str = text.str();
    if (str.size() == 0) {
        ROS_ERROR("Change hardware version : Could not open file %s", file_path.c_str());
        return CHANGE_HW_VERSION_FAIL;
    }

    // replace version in str
    std::string str_search  = "<arg name=\"hardware_version\" default=\"" + std::to_string(old_version);
    std::string str_replace = "<arg name=\"hardware_version\" default=\"" + std::to_string(new_version);
    
    size_t pos = str.find(str_search);
    if (pos == -1) {
        if (str.find(str_replace) != -1) {
            ROS_WARN("Change hardware version : Version is already correct (V%d)", new_version);
            return CHANGE_HW_VERSION_OK;
        }
        ROS_ERROR("Change hardware_version : Malformed gauss_base.launch, can't find hardware version");
        return CHANGE_HW_VERSION_FAIL;
    }
   
    try {
        str.replace(pos, str_search.length(), str_replace);
    }
    catch(const std::out_of_range& e) {
        ROS_INFO("Exception : %s", e.what());
    }

    // close launch file
    in_file.close();

    // re-write launch file
    std::ofstream out_file(file_path.c_str());
    out_file << str;

    ROS_INFO("Successfully changed hardware version in launch file (from V%d to V%d)", old_version, new_version);

    bool reboot;
    ros::param::get("/gauss/reboot_when_auto_change_version", reboot);

    if (reboot) {
        ROS_INFO("Reboot in 1 second...");
        std::system("sleep 1 && sudo reboot&");
    }

    return CHANGE_HW_VERSION_OK;
#endif

    // this function only works on Raspberry Pi 3 board.
    // On other computers, if you run Gauss ROS packages, it means
    // that you are in simulation mode
    // --> if you want to change the hardware version (but you shouldn't have to)
    // you can do it manually on gauss_base.launch
    return CHANGE_HW_VERSION_NOT_ARM; 
}
