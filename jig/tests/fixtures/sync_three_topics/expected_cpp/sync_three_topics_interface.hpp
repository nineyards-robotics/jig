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
#include <message_filters/subscriber.h>
#include <message_filters/synchronizer.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <test_package/sync_three_topics_parameters.hpp>

namespace test_package::sync_three_topics {

template <typename SessionType> struct SyncThreeTopicsPublishers {};

template <typename SessionType> struct SyncThreeTopicsSubscribers {
    std::shared_ptr<jig::Subscriber<nav_msgs::msg::Odometry, SessionType>> odom;

    struct SensorFusion {
        using Policy = message_filters::sync_policies::ApproximateTime<
            sensor_msgs::msg::LaserScan,
            sensor_msgs::msg::Image,
            sensor_msgs::msg::Imu>;
        message_filters::Subscriber<sensor_msgs::msg::LaserScan, rclcpp_lifecycle::LifecycleNode> lidar;
        message_filters::Subscriber<sensor_msgs::msg::Image, rclcpp_lifecycle::LifecycleNode> camera;
        message_filters::Subscriber<sensor_msgs::msg::Imu, rclcpp_lifecycle::LifecycleNode> imu;
        std::shared_ptr<message_filters::Synchronizer<Policy>> sync;

        using Callback = std::function<void(
            std::shared_ptr<SessionType>,
            sensor_msgs::msg::LaserScan::ConstSharedPtr,
            sensor_msgs::msg::Image::ConstSharedPtr,
            sensor_msgs::msg::Imu::ConstSharedPtr)>;
        Callback callback;

        void set_callback(Callback cb) { callback = std::move(cb); }
    } sensor_fusion;
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
        using SensorFusionSyncGroup = typename SyncThreeTopicsSubscribers<SessionType>::SensorFusion;
        sn->subscribers.sensor_fusion.lidar.subscribe(&sn->node, "lidar", rclcpp::QoS(10).best_effort().get_rmw_qos_profile());
        sn->subscribers.sensor_fusion.camera.subscribe(&sn->node, "camera", rclcpp::QoS(5).best_effort().get_rmw_qos_profile());
        sn->subscribers.sensor_fusion.imu.subscribe(&sn->node, "imu", rclcpp::QoS(10).best_effort().get_rmw_qos_profile());
        sn->subscribers.sensor_fusion.sync = std::make_shared<
            message_filters::Synchronizer<typename SensorFusionSyncGroup::Policy>>(
            typename SensorFusionSyncGroup::Policy(20),
            sn->subscribers.sensor_fusion.lidar,
            sn->subscribers.sensor_fusion.camera,
            sn->subscribers.sensor_fusion.imu);
        sn->subscribers.sensor_fusion.sync->setMaxIntervalDuration(rclcpp::Duration::from_seconds(0.1));
        {
            auto weak_sn = std::weak_ptr<SessionType>(sn);
            sn->subscribers.sensor_fusion.sync->registerCallback(
                std::bind(
                    [weak_sn](
                        const sensor_msgs::msg::LaserScan::ConstSharedPtr& msg_0,
                        const sensor_msgs::msg::Image::ConstSharedPtr& msg_1,
                        const sensor_msgs::msg::Imu::ConstSharedPtr& msg_2)
                    {
                        auto sn = weak_sn.lock();
                        if (!sn) return;
                        if (sn->node.get_current_state().id() !=
                            lifecycle_msgs::msg::State::PRIMARY_STATE_ACTIVE) return;
                        if (sn->subscribers.sensor_fusion.callback) {
                            sn->subscribers.sensor_fusion.callback(sn,
                                msg_0,
                                msg_1,
                                msg_2);
                        }
                    },
                    std::placeholders::_1,
                    std::placeholders::_2,
                    std::placeholders::_3));
        }
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
