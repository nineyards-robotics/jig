// auto-generated DO NOT EDIT

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <sensor_msgs/msg/nav_sat_fix.hpp>
#include <jig/base_node.hpp>
#include <jig/session.hpp>
#include <jig/sync_group.hpp>
#include <test_package/sync_approximate_parameters.hpp>

namespace test_package::sync_approximate {

template <typename SessionType> struct SyncApproximatePublishers {};

template <typename SessionType> struct SyncApproximateSubscribers {
    std::shared_ptr<jig::ApproximateSync<SessionType, sensor_msgs::msg::NavSatFix, sensor_msgs::msg::NavSatFix>> dual_fix;
};

template <typename SessionType> struct SyncApproximateServices {};

template <typename SessionType> struct SyncApproximateServiceClients {};

template <typename SessionType> struct SyncApproximateActions {};

template <typename SessionType> struct SyncApproximateActionClients {};

template <typename DerivedSessionType> struct SyncApproximateSession : jig::Session {
    using jig::Session::Session;
    SyncApproximatePublishers<DerivedSessionType> publishers;
    SyncApproximateSubscribers<DerivedSessionType> subscribers;
    SyncApproximateServices<DerivedSessionType> services;
    SyncApproximateServiceClients<DerivedSessionType> service_clients;
    SyncApproximateActions<DerivedSessionType> actions;
    SyncApproximateActionClients<DerivedSessionType> action_clients;
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
class SyncApproximateBase : public jig::BaseNode<"sync_approximate", SessionType, extend_options> {
    static_assert(
        std::is_base_of_v<SyncApproximateSession<SessionType>, SessionType>, "SessionType must be a child of SyncApproximateSession"
    );

  public:
    explicit SyncApproximateBase(const rclcpp::NodeOptions &options)
        : jig::BaseNode<"sync_approximate", SessionType, extend_options>(options) {}

  protected:
    std::shared_ptr<SessionType> create_session(rclcpp_lifecycle::LifecycleNode& node) override {
        auto sn = std::make_shared<SessionType>(node);
        // init parameters (must be before publishers/subscribers for QoS param refs)
        sn->param_listener = std::make_shared<ParamListener>(sn->node.shared_from_this());
        sn->params = sn->param_listener->get_params();

        // init sync group: dual_fix
        sn->subscribers.dual_fix = jig::create_approximate_sync_group<SessionType,
            sensor_msgs::msg::NavSatFix, sensor_msgs::msg::NavSatFix>(
            sn, 10, 0.05,
            std::array<jig::SyncTopicConfig, 2>{
                jig::SyncTopicConfig("fix_left", rclcpp::QoS(10).best_effort()),
                jig::SyncTopicConfig("fix_right", rclcpp::QoS(10).best_effort())
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

} // namespace test_package::sync_approximate
