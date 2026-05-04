#pragma once

#include <chrono>
#include <type_traits>

#include <lifecycle_msgs/msg/state.hpp>
#include <rclcpp/rclcpp.hpp>

#include "compat.hpp"
#include "session.hpp"

namespace jig {

/// Create a timer that fires a session-aware callback at the given period.
///
/// The timer is created in a **cancelled** state and will be started automatically
/// by the lifecycle activate transition. To start it manually, call `timer->reset()`.
///
/// The callback only fires while the node is in the ACTIVE lifecycle state.
/// The timer is automatically registered with the session for lifecycle management
/// (cancelled on deactivate, reset on activate).
template <typename DurationRepT, typename DurationT, typename SessionType, typename CallbackT>
auto create_timer(
    std::shared_ptr<SessionType> sn,
    std::chrono::duration<DurationRepT, DurationT> period,
    CallbackT callback,
    rclcpp::CallbackGroup::SharedPtr group = nullptr
) {
    static_assert(std::is_base_of_v<Session, SessionType>, "SessionType must derive from jig::Session");

    std::weak_ptr<SessionType> weak_sn = sn;
    auto cb = [weak_sn, callback]() {
        auto sn = weak_sn.lock();
        if (!sn)
            return;
        if (sn->node.get_current_state().id() == lifecycle_msgs::msg::State::PRIMARY_STATE_ACTIVE) {
            callback(sn);
        }
    };
#if JIG_HAS_TIMER_AUTOSTART
    auto timer = rclcpp::create_timer(
        sn->node.shared_from_this(),
        sn->node.get_clock(),
        rclcpp::Duration(period),
        std::move(cb),
        group,
        /*autostart=*/false
    );
#else
    // Move cb in: rclcpp::create_timer takes the callback by forwarding
    // reference, so passing an lvalue deduces CallbackT to a reference type
    // and GenericTimer<CB&> stores the callback by reference — into a
    // local that dies when this function returns. SIGSEGV on first fire.
    auto timer = rclcpp::create_timer(
        sn->node.shared_from_this(), sn->node.get_clock(), rclcpp::Duration(period), std::move(cb), group
    );
    timer->cancel();
#endif

    sn->timers.push_back(timer);
    return timer;
}

/// Create a wall timer that fires a session-aware callback at the given period.
///
/// The timer is created in a **cancelled** state and will be started automatically
/// by the lifecycle activate transition. To start it manually, call `timer->reset()`.
///
/// The callback only fires while the node is in the ACTIVE lifecycle state.
/// The timer is automatically registered with the session for lifecycle management
/// (cancelled on deactivate, reset on activate).
template <typename DurationRepT, typename DurationT, typename SessionType, typename CallbackT>
auto create_wall_timer(
    std::shared_ptr<SessionType> sn,
    std::chrono::duration<DurationRepT, DurationT> period,
    CallbackT callback,
    rclcpp::CallbackGroup::SharedPtr group = nullptr
) {
    static_assert(std::is_base_of_v<Session, SessionType>, "SessionType must derive from jig::Session");

    std::weak_ptr<SessionType> weak_sn = sn;
    auto cb = [weak_sn, callback]() {
        auto sn = weak_sn.lock();
        if (!sn)
            return;
        if (sn->node.get_current_state().id() == lifecycle_msgs::msg::State::PRIMARY_STATE_ACTIVE) {
            callback(sn);
        }
    };
#if JIG_HAS_TIMER_AUTOSTART
    auto timer = rclcpp::create_wall_timer(
        period,
        std::move(cb),
        group,
        sn->node.get_node_base_interface().get(),
        sn->node.get_node_timers_interface().get(),
        /*autostart=*/false
    );
#else
    auto timer = rclcpp::create_wall_timer(
        period,
        std::move(cb),
        group,
        sn->node.get_node_base_interface().get(),
        sn->node.get_node_timers_interface().get()
    );
    timer->cancel();
#endif

    sn->timers.push_back(timer);
    return timer;
}

} // namespace jig
