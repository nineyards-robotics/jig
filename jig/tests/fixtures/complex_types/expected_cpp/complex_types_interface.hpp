// auto-generated DO NOT EDIT

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <nav_msgs/msg/path.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <jig/base_node.hpp>
#include <jig/session.hpp>
#include <jig/publisher.hpp>
#include <jig/subscriber.hpp>
#include <jig/default_qos_handlers.hpp>
#include <test_package/complex_types_parameters.hpp>

namespace test_package::complex_types {

template <typename SessionType> struct ComplexTypesPublishers {
    std::shared_ptr<jig::Publisher<geometry_msgs::msg::PoseStamped, SessionType>> pose;
    std::shared_ptr<jig::Publisher<nav_msgs::msg::Path, SessionType>> path;
};

template <typename SessionType> struct ComplexTypesSubscribers {
    std::shared_ptr<jig::Subscriber<sensor_msgs::msg::JointState, SessionType>> joint_states;
    std::shared_ptr<jig::Subscriber<sensor_msgs::msg::PointCloud2, SessionType>> point_cloud;
};

template <typename SessionType> struct ComplexTypesServices {};

template <typename SessionType> struct ComplexTypesServiceClients {};

template <typename SessionType> struct ComplexTypesActions {};

template <typename SessionType> struct ComplexTypesActionClients {};

template <typename DerivedSessionType> struct ComplexTypesSession : jig::Session {
    using jig::Session::Session;
    ComplexTypesPublishers<DerivedSessionType> publishers;
    ComplexTypesSubscribers<DerivedSessionType> subscribers;
    ComplexTypesServices<DerivedSessionType> services;
    ComplexTypesServiceClients<DerivedSessionType> service_clients;
    ComplexTypesActions<DerivedSessionType> actions;
    ComplexTypesActionClients<DerivedSessionType> action_clients;
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
class ComplexTypesBase : public jig::BaseNode<"complex_types", SessionType, extend_options> {
    static_assert(
        std::is_base_of_v<ComplexTypesSession<SessionType>, SessionType>, "SessionType must be a child of ComplexTypesSession"
    );

  public:
    explicit ComplexTypesBase(const rclcpp::NodeOptions &options)
        : jig::BaseNode<"complex_types", SessionType, extend_options>(options) {}

  protected:
    std::shared_ptr<SessionType> create_session(rclcpp_lifecycle::LifecycleNode& node) override {
        auto sn = std::make_shared<SessionType>(node);
        // init parameters (must be before publishers/subscribers for QoS param refs)
        sn->param_listener = std::make_shared<ParamListener>(sn->node.shared_from_this());
        sn->params = sn->param_listener->get_params();

        // init publishers
        sn->publishers.pose = jig::create_publisher<geometry_msgs::msg::PoseStamped>(sn, "pose", rclcpp::QoS(10).reliable());
        sn->publishers.path = jig::create_publisher<nav_msgs::msg::Path>(sn, "path", rclcpp::QoS(5).reliable());
        // init subscribers
        sn->subscribers.joint_states = jig::create_subscriber<sensor_msgs::msg::JointState>(sn, "joint_states", rclcpp::QoS(10).best_effort());
        jig::attach_default_qos_handlers(sn->subscribers.joint_states);
        sn->subscribers.point_cloud = jig::create_subscriber<sensor_msgs::msg::PointCloud2>(sn, "point_cloud", rclcpp::QoS(1).best_effort());
        jig::attach_default_qos_handlers(sn->subscribers.point_cloud);
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

} // namespace test_package::complex_types
