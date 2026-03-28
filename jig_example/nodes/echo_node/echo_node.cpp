#include "echo_node.hpp"

#include <memory>
#include <rclcpp/logging.hpp>
#include <string>

#include "example_interfaces/srv/add_two_ints.hpp"
#include "example_interfaces/srv/trigger.hpp"
#include "std_msgs/msg/string.hpp"

#include <jig/timer.hpp>

using namespace std::chrono_literals;

namespace jig_example::echo_node {

void input_callback(std::shared_ptr<Session> sn, std_msgs::msg::String::ConstSharedPtr msg) {
    auto out = std_msgs::msg::String();
    out.data = sn->params.message_prefix + ": " + msg->data;
    sn->publishers.output->publish(out);

    auto prefixed = std_msgs::msg::String();
    prefixed.data = out.data;
    sn->publishers.prefixed_output->publish(prefixed);
}

void add_two_ints_handler(
    std::shared_ptr<Session> /*sn*/,
    example_interfaces::srv::AddTwoInts::Request::SharedPtr request,
    example_interfaces::srv::AddTwoInts::Response::SharedPtr response
) {
    response->sum = request->a + request->b;
}

void get_counter_handler(
    std::shared_ptr<Session> sn,
    example_interfaces::srv::Trigger::Request::SharedPtr /*request*/,
    example_interfaces::srv::Trigger::Response::SharedPtr response
) {
    response->success = true;
    response->message = sn->params.message_prefix + ": counter=" + std::to_string(sn->counter);
}

void timer_callback(std::shared_ptr<Session> sn) {
    sn->counter++;
    auto msg = std_msgs::msg::String();
    msg.data = sn->params.message_prefix + ": " + std::to_string(sn->counter);
    sn->publishers.output->publish(msg);
}

CallbackReturn on_configure(std::shared_ptr<Session> sn) {
    sn->subscribers.input->set_callback(input_callback);
    sn->services.add_two_ints->set_request_handler(add_two_ints_handler);
    sn->services.get_counter->set_request_handler(get_counter_handler);

    jig::create_timer(sn, std::chrono::milliseconds(sn->params.publish_rate_ms), timer_callback);

    return CallbackReturn::SUCCESS;
}

} // namespace jig_example::echo_node
