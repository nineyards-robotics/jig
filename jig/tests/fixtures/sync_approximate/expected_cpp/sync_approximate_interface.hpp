// auto-generated DO NOT EDIT

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <sensor_msgs/msg/nav_sat_fix.hpp>
#include <jig/base_node.hpp>
#include <jig/session.hpp>
#include <message_filters/subscriber.h>
#include <message_filters/synchronizer.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <test_package/sync_approximate_parameters.hpp>

namespace test_package::sync_approximate {

template <typename SessionType> struct SyncApproximatePublishers {};

template <typename SessionType> struct SyncApproximateSubscribers {

    struct DualFix {
        using Policy = message_filters::sync_policies::ApproximateTime<
            sensor_msgs::msg::NavSatFix,
            sensor_msgs::msg::NavSatFix>;
        message_filters::Subscriber<sensor_msgs::msg::NavSatFix, rclcpp_lifecycle::LifecycleNode> fix_left;
        message_filters::Subscriber<sensor_msgs::msg::NavSatFix, rclcpp_lifecycle::LifecycleNode> fix_right;
        std::shared_ptr<message_filters::Synchronizer<Policy>> sync;

        using Callback = std::function<void(
            std::shared_ptr<SessionType>,
            sensor_msgs::msg::NavSatFix::ConstSharedPtr,
            sensor_msgs::msg::NavSatFix::ConstSharedPtr)>;
        Callback callback;

        void set_callback(Callback cb) { callback = std::move(cb); }
    } dual_fix;
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
        using DualFixSyncGroup = typename SyncApproximateSubscribers<SessionType>::DualFix;
        sn->subscribers.dual_fix.fix_left.subscribe(&sn->node, "fix_left", rclcpp::QoS(10).best_effort().get_rmw_qos_profile());
        sn->subscribers.dual_fix.fix_right.subscribe(&sn->node, "fix_right", rclcpp::QoS(10).best_effort().get_rmw_qos_profile());
        sn->subscribers.dual_fix.sync = std::make_shared<
            message_filters::Synchronizer<typename DualFixSyncGroup::Policy>>(
            typename DualFixSyncGroup::Policy(10),
            sn->subscribers.dual_fix.fix_left,
            sn->subscribers.dual_fix.fix_right);
        sn->subscribers.dual_fix.sync->setMaxIntervalDuration(rclcpp::Duration::from_seconds(0.05));
        {
            auto weak_sn = std::weak_ptr<SessionType>(sn);
            sn->subscribers.dual_fix.sync->registerCallback(
                std::bind(
                    [weak_sn](
                        const sensor_msgs::msg::NavSatFix::ConstSharedPtr& msg_0,
                        const sensor_msgs::msg::NavSatFix::ConstSharedPtr& msg_1)
                    {
                        auto sn = weak_sn.lock();
                        if (!sn) return;
                        if (sn->node.get_current_state().id() !=
                            lifecycle_msgs::msg::State::PRIMARY_STATE_ACTIVE) return;
                        if (sn->subscribers.dual_fix.callback) {
                            sn->subscribers.dual_fix.callback(sn,
                                msg_0,
                                msg_1);
                        }
                    },
                    std::placeholders::_1,
                    std::placeholders::_2));
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

} // namespace test_package::sync_approximate
