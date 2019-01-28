#include "gauss_driver/stepper/gauss_can_driver.h"

GaussCanDriver::GaussCanDriver(int spi_channel, int spi_baudrate, INT8U gpio_can_interrupt) {
    mcp_can.reset(new MCP_CAN(spi_channel, spi_baudrate, gpio_can_interrupt)); 
}

bool GaussCanDriver::setupInterruptGpio()
{
    if (!mcp_can->setupInterruptGpio()) {
        printf("Failed to start gpio");
        return CAN_GPIO_FAILINIT;
    }
    return CAN_OK;
}

bool GaussCanDriver::setupSpi()
{
    if (!mcp_can->setupSpi()) {
        printf("Failed to start spi");
        return CAN_SPI_FAILINIT;
    }
    return CAN_OK;
}

INT8U GaussCanDriver::init()
{
    // no mask or filter used, receive all messages from CAN bus
    // messages with ids != motor_id will be sent to another ROS interface
    // so we can use many CAN devices with this only driver
    int result = mcp_can->begin(MCP_ANY, CAN_1000KBPS, MCP_8MHZ);
    ROS_INFO("Result begin can : %d", result);
    
    if (result != CAN_OK) { 
        ROS_ERROR("Failed to init MCP2515 (CAN bus)");
        return result; 
    }
    
    // set mode to normal
    mcp_can->setMode(MCP_NORMAL);
    
    ros::Duration(0.05).sleep();
    return result;
}

bool GaussCanDriver::canReadData()
{
    return mcp_can->canReadData();
}

INT8U GaussCanDriver::readMsgBuf(INT32U *id, INT8U *len, INT8U *buf)
{
    return mcp_can->readMsgBuf(id, len, buf);
}

INT8U GaussCanDriver::sendPositionCommand(int id, int cmd)
{
    uint8_t data[4] = { CAN_CMD_POSITION , (uint8_t) ((cmd >> 16) & 0xFF),
        (uint8_t) ((cmd >> 8) & 0xFF), (uint8_t) (cmd & 0XFF) };
    return mcp_can->sendMsgBuf(id, 0, 4, data);
}

INT8U GaussCanDriver::sendRelativeMoveCommand(int id, int steps, int delay)
{
    uint8_t data[7] = { CAN_CMD_MOVE_REL, 
        (uint8_t) ((steps >> 16) & 0xFF), (uint8_t) ((steps >> 8) & 0xFF), (uint8_t) (steps & 0XFF),
        (uint8_t) ((delay >> 16) & 0xFF), (uint8_t) ((delay >> 8) & 0xFF), (uint8_t) (delay & 0XFF)};
    return mcp_can->sendMsgBuf(id, 0, 7, data);
}

INT8U GaussCanDriver::sendTorqueOnCommand(int id, int torque_on)
{
    uint8_t data[2] = {0};
    data[0] = CAN_CMD_MODE;
    data[1] = (torque_on) ? STEPPER_CONTROL_MODE_STANDARD : STEPPER_CONTROL_MODE_RELAX; 
    return mcp_can->sendMsgBuf(id, 0, 2, data);
}

INT8U GaussCanDriver::sendPositionOffsetCommand(int id, int cmd) 
{
    uint8_t data[4] = { CAN_CMD_OFFSET , (uint8_t) ((cmd >> 16) & 0xFF),
        (uint8_t) ((cmd >> 8) & 0xFF), (uint8_t) (cmd & 0XFF) };
    return mcp_can->sendMsgBuf(id, 0, 4, data);
}

INT8U GaussCanDriver::sendCalibrationCommand(int id, int offset, int delay, int direction, int timeout)
{
    direction = (direction == 1) ? 1 : 0;

    uint8_t data[8] = { CAN_CMD_CALIBRATE , (uint8_t) ((offset >> 16) & 0xFF),
        (uint8_t) ((offset >> 8) & 0xFF), (uint8_t) (offset & 0XFF),
        (uint8_t) ((delay >> 8) & 0xFF), (uint8_t) (delay & 0xFF), 
        (uint8_t)direction, (uint8_t)timeout };
    return mcp_can->sendMsgBuf(id, 0, 8, data);
}

INT8U GaussCanDriver::sendSynchronizePositionCommand(int id, bool begin_traj)
{
    uint8_t data[2] = { CAN_CMD_SYNCHRONIZE, (uint8_t) begin_traj };
    return mcp_can->sendMsgBuf(id, 0, 2, data);
}
   
INT8U GaussCanDriver::sendMicroStepsCommand(int id, int micro_steps)
{
    uint8_t data[2] = { CAN_CMD_MICRO_STEPS, (uint8_t) micro_steps };
    return mcp_can->sendMsgBuf(id, 0, 2, data);
}

INT8U GaussCanDriver::sendMaxEffortCommand(int id, int effort)
{
    uint8_t data[3] = { CAN_CMD_MAX_EFFORT, (uint8_t)((effort>>8) & 0xFF), (uint8_t)(effort & 0xFF)};
    return mcp_can->sendMsgBuf(id, 0, 3, data);
}
