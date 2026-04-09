#pragma once

#include <array>
#include <functional>
#include <memory>
#include <string>
#include <tuple>
#include <type_traits>
#include <utility>

#include <lifecycle_msgs/msg/state.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>

// Kilted+ moved to .hpp headers and deprecated the old .h shims.
// Use __has_include so we keep building on Humble/Jazzy where only .h exists.
#if __has_include(<message_filters/sync_policies/approximate_time.hpp>)
#include <message_filters/subscriber.hpp>
#include <message_filters/sync_policies/approximate_time.hpp>
#include <message_filters/sync_policies/exact_time.hpp>
#include <message_filters/synchronizer.hpp>
#else
#include <message_filters/subscriber.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <message_filters/sync_policies/exact_time.h>
#include <message_filters/synchronizer.h>
#endif

#include "session.hpp"

namespace jig {

namespace detail {
// Custom placeholder type for variadic std::bind expansion.
// message_filters::registerCallback needs std::bind with explicit placeholders
// to deduce callback arity — std::function alone is not sufficient.
template <int N> struct Placeholder {};
} // namespace detail

} // namespace jig

// Enable our custom placeholder for std::bind
namespace std {
template <int N> struct is_placeholder<jig::detail::Placeholder<N>> : std::integral_constant<int, N> {};
} // namespace std

namespace jig {

struct SyncTopicConfig {
    std::string name;
    rclcpp::QoS qos;
    SyncTopicConfig(std::string name, rclcpp::QoS qos) : name(std::move(name)), qos(std::move(qos)) {}
};

template <typename SessionType, typename PolicyT, typename... MessageTs> class SyncGroup {
    static_assert(std::is_base_of_v<Session, SessionType>, "SessionType must derive from jig::Session");
    static constexpr size_t NumTopics = sizeof...(MessageTs);

  public:
    using Callback = std::function<void(std::shared_ptr<SessionType>, typename MessageTs::ConstSharedPtr...)>;

    explicit SyncGroup(
        std::shared_ptr<SessionType> sn, size_t queue_size, std::array<SyncTopicConfig, NumTopics> configs
    )
        : session_(sn) {
        subscribe_all(&sn->node, configs, std::index_sequence_for<MessageTs...>{});
        create_sync(queue_size, std::index_sequence_for<MessageTs...>{});
        register_callback(std::index_sequence_for<MessageTs...>{});
    }

    void set_max_interval(double seconds) {
        if (sync_) {
            sync_->setMaxIntervalDuration(rclcpp::Duration::from_seconds(seconds));
        }
    }

    void set_callback(Callback cb) { callback_ = std::move(cb); }

  private:
    std::weak_ptr<SessionType> session_;
    std::tuple<message_filters::Subscriber<MessageTs, rclcpp_lifecycle::LifecycleNode>...> subscribers_;
    std::shared_ptr<message_filters::Synchronizer<PolicyT>> sync_;
    Callback callback_;

    template <std::size_t... Is>
    void
    subscribe_all(rclcpp_lifecycle::LifecycleNode *node, const std::array<SyncTopicConfig, NumTopics> &configs, std::index_sequence<Is...>) {
        (std::get<Is>(subscribers_).subscribe(node, configs[Is].name, configs[Is].qos.get_rmw_qos_profile()), ...);
    }

    template <std::size_t... Is> void create_sync(size_t queue_size, std::index_sequence<Is...>) {
        sync_ = std::make_shared<message_filters::Synchronizer<PolicyT>>(
            PolicyT(queue_size), std::get<Is>(subscribers_)...
        );
    }

    template <std::size_t... Is> void register_callback(std::index_sequence<Is...>) {
        sync_->registerCallback(std::bind(
            [this](const typename MessageTs::ConstSharedPtr &...msgs) {
                auto sn = session_.lock();
                if (!sn)
                    return;
                if (sn->node.get_current_state().id() != lifecycle_msgs::msg::State::PRIMARY_STATE_ACTIVE)
                    return;
                if (callback_) {
                    callback_(sn, msgs...);
                }
            },
            detail::Placeholder<static_cast<int>(Is) + 1>{}...
        ));
    }
};

// Convenience type aliases
template <typename SessionType, typename... MessageTs>
using ApproximateSync =
    SyncGroup<SessionType, message_filters::sync_policies::ApproximateTime<MessageTs...>, MessageTs...>;

template <typename SessionType, typename... MessageTs>
using ExactSync = SyncGroup<SessionType, message_filters::sync_policies::ExactTime<MessageTs...>, MessageTs...>;

// Factory functions matching the jig::create_subscriber / jig::create_publisher pattern
template <typename SessionType, typename... MessageTs>
std::shared_ptr<ApproximateSync<SessionType, MessageTs...>> create_approximate_sync_group(
    std::shared_ptr<SessionType> sn,
    size_t queue_size,
    double max_interval,
    std::array<SyncTopicConfig, sizeof...(MessageTs)> configs
) {
    auto group = std::make_shared<ApproximateSync<SessionType, MessageTs...>>(sn, queue_size, std::move(configs));
    group->set_max_interval(max_interval);
    return group;
}

template <typename SessionType, typename... MessageTs>
std::shared_ptr<ExactSync<SessionType, MessageTs...>> create_exact_sync_group(
    std::shared_ptr<SessionType> sn, size_t queue_size, std::array<SyncTopicConfig, sizeof...(MessageTs)> configs
) {
    return std::make_shared<ExactSync<SessionType, MessageTs...>>(sn, queue_size, std::move(configs));
}

} // namespace jig
