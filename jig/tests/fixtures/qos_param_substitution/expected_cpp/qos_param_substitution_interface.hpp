// auto-generated DO NOT EDIT

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>
#include <std_msgs/msg/string.hpp>
#include <jig/base_node.hpp>
#include <jig/session.hpp>
#include <jig/publisher.hpp>
#include <jig/subscriber.hpp>
#include <jig/default_qos_handlers.hpp>
#include <jig/qos_helpers.hpp>
#include <test_package/qos_param_substitution_parameters.hpp>

namespace test_package::qos_param_substitution {

template <typename SessionType> struct QosParamSubstitutionPublishers {
    std::shared_ptr<jig::Publisher<std_msgs::msg::String, SessionType>> processed_data;
};

template <typename SessionType> struct QosParamSubstitutionSubscribers {
    std::shared_ptr<jig::Subscriber<sensor_msgs::msg::LaserScan, SessionType>> sensor_data;
};

template <typename SessionType> struct QosParamSubstitutionServices {};

template <typename SessionType> struct QosParamSubstitutionServiceClients {};

template <typename SessionType> struct QosParamSubstitutionActions {};

template <typename SessionType> struct QosParamSubstitutionActionClients {};

template <typename DerivedSessionType> struct QosParamSubstitutionSession : jig::Session {
    using jig::Session::Session;
    QosParamSubstitutionPublishers<DerivedSessionType> publishers;
    QosParamSubstitutionSubscribers<DerivedSessionType> subscribers;
    QosParamSubstitutionServices<DerivedSessionType> services;
    QosParamSubstitutionServiceClients<DerivedSessionType> service_clients;
    QosParamSubstitutionActions<DerivedSessionType> actions;
    QosParamSubstitutionActionClients<DerivedSessionType> action_clients;
    std::shared_ptr<ParamListener> param_listener;
    Params params;
};

using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

template <
    typename SessionType,
    auto on_configure_func,
    auto on_activate_func = [](std::shared_ptr<SessionType>) { return CallbackReturn::SUCCESS; },
    auto on_deactivate_func = [](std::shared_ptr<SessionType>) { return CallbackReturn::SUCCESS; },
    auto on_cleanup_func = [](std::shared_ptr<SessionType>) { return CallbackReturn::SUCCESS; },
    auto on_shutdown_func = [](std::shared_ptr<SessionType>) {},
    auto extend_options = [](rclcpp::NodeOptions options) { return options; }>
class QosParamSubstitutionBase : public jig::BaseNode<"qos_param_substitution", SessionType, extend_options> {
    static_assert(
        std::is_base_of_v<QosParamSubstitutionSession<SessionType>, SessionType>, "SessionType must be a child of QosParamSubstitutionSession"
    );

  public:
    explicit QosParamSubstitutionBase(const rclcpp::NodeOptions &options)
        : jig::BaseNode<"qos_param_substitution", SessionType, extend_options>(options) {}

  protected:
    std::shared_ptr<SessionType> create_session(rclcpp_lifecycle::LifecycleNode& node) override {
        auto sn = std::make_shared<SessionType>(node);
        // init parameters (must be before publishers/subscribers for QoS param refs)
        sn->param_listener = std::make_shared<ParamListener>(sn->node.shared_from_this());
        sn->params = sn->param_listener->get_params();

        // init publishers
        sn->publishers.processed_data = jig::create_publisher<std_msgs::msg::String>(sn, "/processed_data", rclcpp::QoS(sn->params.output_queue_depth).reliable());
        // init subscribers
        sn->subscribers.sensor_data = jig::create_subscriber<sensor_msgs::msg::LaserScan>(sn, "/sensor_data", rclcpp::QoS(sn->params.sensor_queue_depth).reliability(jig::to_reliability(sn->params.sensor_reliability)).durability(jig::to_durability(sn->params.sensor_durability)).deadline(rclcpp::Duration::from_nanoseconds(sn->params.sensor_deadline_ms * 1000000LL)).liveliness(jig::to_liveliness(sn->params.sensor_liveliness)));
        jig::attach_default_qos_handlers(sn->subscribers.sensor_data);
        return sn;
    }

    void activate_entities(std::shared_ptr<SessionType> sn) override {
        for (auto &t : sn->timers) { t->reset(); }
    }

    void deactivate_entities(std::shared_ptr<SessionType> sn) override {
        for (auto &t : sn->timers) { t->cancel(); }
    }

    CallbackReturn user_on_configure(std::shared_ptr<SessionType> sn) override { return on_configure_func(sn); }
    CallbackReturn user_on_activate(std::shared_ptr<SessionType> sn) override { return on_activate_func(sn); }
    CallbackReturn user_on_deactivate(std::shared_ptr<SessionType> sn) override { return on_deactivate_func(sn); }
    CallbackReturn user_on_cleanup(std::shared_ptr<SessionType> sn) override { return on_cleanup_func(sn); }
    void user_on_shutdown(std::shared_ptr<SessionType> sn) override { on_shutdown_func(sn); }
};

} // namespace test_package::qos_param_substitution
