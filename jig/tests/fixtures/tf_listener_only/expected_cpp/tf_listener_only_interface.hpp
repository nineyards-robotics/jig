// auto-generated DO NOT EDIT

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <jig/base_node.hpp>
#include <jig/session.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <test_package/tf_listener_only_parameters.hpp>

namespace test_package::tf_listener_only {

template <typename SessionType> struct TfListenerOnlyPublishers {};

template <typename SessionType> struct TfListenerOnlySubscribers {};

template <typename SessionType> struct TfListenerOnlyServices {};

template <typename SessionType> struct TfListenerOnlyServiceClients {};

template <typename SessionType> struct TfListenerOnlyActions {};

template <typename SessionType> struct TfListenerOnlyActionClients {};

template <typename DerivedSessionType> struct TfListenerOnlySession : jig::Session {
    using jig::Session::Session;
    TfListenerOnlyPublishers<DerivedSessionType> publishers;
    TfListenerOnlySubscribers<DerivedSessionType> subscribers;
    TfListenerOnlyServices<DerivedSessionType> services;
    TfListenerOnlyServiceClients<DerivedSessionType> service_clients;
    TfListenerOnlyActions<DerivedSessionType> actions;
    TfListenerOnlyActionClients<DerivedSessionType> action_clients;
    std::shared_ptr<tf2_ros::Buffer> tf_buffer;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener;
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
class TfListenerOnlyBase : public jig::BaseNode<"tf_listener_only", SessionType, extend_options> {
    static_assert(
        std::is_base_of_v<TfListenerOnlySession<SessionType>, SessionType>, "SessionType must be a child of TfListenerOnlySession"
    );

  public:
    explicit TfListenerOnlyBase(const rclcpp::NodeOptions &options)
        : jig::BaseNode<"tf_listener_only", SessionType, extend_options>(options) {}

  protected:
    std::shared_ptr<SessionType> create_session(rclcpp_lifecycle::LifecycleNode& node) override {
        auto sn = std::make_shared<SessionType>(node);
        // init parameters (must be before publishers/subscribers for QoS param refs)
        sn->param_listener = std::make_shared<ParamListener>(sn->node.shared_from_this());
        sn->params = sn->param_listener->get_params();

        // init tf
        sn->tf_buffer = std::make_shared<tf2_ros::Buffer>(sn->node.get_clock());
        sn->tf_listener = std::make_shared<tf2_ros::TransformListener>(*sn->tf_buffer, &sn->node);
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

} // namespace test_package::tf_listener_only
