// auto-generated DO NOT EDIT

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <jig/base_node.hpp>
#include <jig/session.hpp>
#include <message_filters/subscriber.h>
#include <message_filters/synchronizer.h>
#include <message_filters/sync_policies/exact_time.h>
#include <test_package/sync_exact_parameters.hpp>

namespace test_package::sync_exact {

template <typename SessionType> struct SyncExactPublishers {};

template <typename SessionType> struct SyncExactSubscribers {

    struct StereoPair {
        using Policy = message_filters::sync_policies::ExactTime<
            sensor_msgs::msg::Image,
            sensor_msgs::msg::Image>;
        message_filters::Subscriber<sensor_msgs::msg::Image, rclcpp_lifecycle::LifecycleNode> camera_left;
        message_filters::Subscriber<sensor_msgs::msg::Image, rclcpp_lifecycle::LifecycleNode> camera_right;
        std::shared_ptr<message_filters::Synchronizer<Policy>> sync;

        using Callback = std::function<void(
            std::shared_ptr<SessionType>,
            sensor_msgs::msg::Image::ConstSharedPtr,
            sensor_msgs::msg::Image::ConstSharedPtr)>;
        Callback callback;

        void set_callback(Callback cb) { callback = std::move(cb); }
    } stereo_pair;
};

template <typename SessionType> struct SyncExactServices {};

template <typename SessionType> struct SyncExactServiceClients {};

template <typename SessionType> struct SyncExactActions {};

template <typename SessionType> struct SyncExactActionClients {};

template <typename DerivedSessionType> struct SyncExactSession : jig::Session {
    using jig::Session::Session;
    SyncExactPublishers<DerivedSessionType> publishers;
    SyncExactSubscribers<DerivedSessionType> subscribers;
    SyncExactServices<DerivedSessionType> services;
    SyncExactServiceClients<DerivedSessionType> service_clients;
    SyncExactActions<DerivedSessionType> actions;
    SyncExactActionClients<DerivedSessionType> action_clients;
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
class SyncExactBase : public jig::BaseNode<"sync_exact", SessionType, extend_options> {
    static_assert(
        std::is_base_of_v<SyncExactSession<SessionType>, SessionType>, "SessionType must be a child of SyncExactSession"
    );

  public:
    explicit SyncExactBase(const rclcpp::NodeOptions &options)
        : jig::BaseNode<"sync_exact", SessionType, extend_options>(options) {}

  protected:
    std::shared_ptr<SessionType> create_session(rclcpp_lifecycle::LifecycleNode& node) override {
        auto sn = std::make_shared<SessionType>(node);
        // init parameters (must be before publishers/subscribers for QoS param refs)
        sn->param_listener = std::make_shared<ParamListener>(sn->node.shared_from_this());
        sn->params = sn->param_listener->get_params();

        // init sync group: stereo_pair
        using StereoPairSyncGroup = typename SyncExactSubscribers<SessionType>::StereoPair;
        sn->subscribers.stereo_pair.camera_left.subscribe(&sn->node, "camera_left", rclcpp::QoS(5).reliable().get_rmw_qos_profile());
        sn->subscribers.stereo_pair.camera_right.subscribe(&sn->node, "camera_right", rclcpp::QoS(5).reliable().get_rmw_qos_profile());
        sn->subscribers.stereo_pair.sync = std::make_shared<
            message_filters::Synchronizer<typename StereoPairSyncGroup::Policy>>(
            typename StereoPairSyncGroup::Policy(5),
            sn->subscribers.stereo_pair.camera_left,
            sn->subscribers.stereo_pair.camera_right);
        {
            auto weak_sn = std::weak_ptr<SessionType>(sn);
            sn->subscribers.stereo_pair.sync->registerCallback(
                std::bind(
                    [weak_sn](
                        const sensor_msgs::msg::Image::ConstSharedPtr& msg_0,
                        const sensor_msgs::msg::Image::ConstSharedPtr& msg_1)
                    {
                        auto sn = weak_sn.lock();
                        if (!sn) return;
                        if (sn->node.get_current_state().id() !=
                            lifecycle_msgs::msg::State::PRIMARY_STATE_ACTIVE) return;
                        if (sn->subscribers.stereo_pair.callback) {
                            sn->subscribers.stereo_pair.callback(sn,
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

} // namespace test_package::sync_exact
