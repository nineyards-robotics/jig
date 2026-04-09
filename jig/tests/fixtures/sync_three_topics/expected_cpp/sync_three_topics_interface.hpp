// auto-generated DO NOT EDIT

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>
#include <jig/base_node.hpp>
#include <jig/session.hpp>
#include <jig/subscriber.hpp>
#include <jig/default_qos_handlers.hpp>
#include <jig/sync_group.hpp>
#include <test_package/sync_three_topics_parameters.hpp>

namespace test_package::sync_three_topics {

template <typename SessionType> struct SyncThreeTopicsPublishers {};

template <typename SessionType> struct SyncThreeTopicsSubscribers {
    std::shared_ptr<jig::Subscriber<nav_msgs::msg::Odometry, SessionType>> odom;
    std::shared_ptr<jig::ApproximateSync<SessionType, sensor_msgs::msg::LaserScan, sensor_msgs::msg::Image, sensor_msgs::msg::Imu>> sensor_fusion;
};

template <typename SessionType> struct SyncThreeTopicsServices {};

template <typename SessionType> struct SyncThreeTopicsServiceClients {};

template <typename SessionType> struct SyncThreeTopicsActions {};

template <typename SessionType> struct SyncThreeTopicsActionClients {};

template <typename DerivedSessionType> struct SyncThreeTopicsSession : jig::Session {
    using jig::Session::Session;
    SyncThreeTopicsPublishers<DerivedSessionType> publishers;
    SyncThreeTopicsSubscribers<DerivedSessionType> subscribers;
    SyncThreeTopicsServices<DerivedSessionType> services;
    SyncThreeTopicsServiceClients<DerivedSessionType> service_clients;
    SyncThreeTopicsActions<DerivedSessionType> actions;
    SyncThreeTopicsActionClients<DerivedSessionType> action_clients;
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
class SyncThreeTopicsBase : public jig::BaseNode<"sync_three_topics", SessionType, extend_options> {
    static_assert(
        std::is_base_of_v<SyncThreeTopicsSession<SessionType>, SessionType>, "SessionType must be a child of SyncThreeTopicsSession"
    );

  public:
    explicit SyncThreeTopicsBase(const rclcpp::NodeOptions &options)
        : jig::BaseNode<"sync_three_topics", SessionType, extend_options>(options) {}

  protected:
    std::shared_ptr<SessionType> create_session(rclcpp_lifecycle::LifecycleNode& node) override {
        auto sn = std::make_shared<SessionType>(node);
        // init parameters (must be before publishers/subscribers for QoS param refs)
        sn->param_listener = std::make_shared<ParamListener>(sn->node.shared_from_this());
        sn->params = sn->param_listener->get_params();
        // init subscribers
        sn->subscribers.odom = jig::create_subscriber<nav_msgs::msg::Odometry>(sn, "odom", rclcpp::QoS(1).reliable());
        jig::attach_default_qos_handlers(sn->subscribers.odom);

        // init sync group: sensor_fusion
        sn->subscribers.sensor_fusion = jig::create_approximate_sync_group<SessionType,
            sensor_msgs::msg::LaserScan, sensor_msgs::msg::Image, sensor_msgs::msg::Imu>(
            sn, 20, 0.1,
            std::array<jig::SyncTopicConfig, 3>{
                jig::SyncTopicConfig("lidar", rclcpp::QoS(10).best_effort()),
                jig::SyncTopicConfig("camera", rclcpp::QoS(5).best_effort()),
                jig::SyncTopicConfig("imu", rclcpp::QoS(10).best_effort())
            });
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

} // namespace test_package::sync_three_topics
