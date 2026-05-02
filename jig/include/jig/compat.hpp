#pragma once

#include <rclcpp/qos.hpp>
#include <rclcpp/version.h>

// Humble's rclcpp is at major version 16. Jazzy onwards (28+) added rclcpp::QoS
// overloads to LifecycleNode::create_service / create_client; on Humble these
// methods only accept rmw_qos_profile_t, so we have to unwrap.
#if RCLCPP_VERSION_GTE(20, 0, 0)
#define JIG_LIFECYCLE_QOS(qos) (qos)
#else
#define JIG_LIFECYCLE_QOS(qos) ((qos).get_rmw_qos_profile())
#endif

// rclcpp::create_timer / create_wall_timer gained an autostart parameter in
// Jazzy (rclcpp 28.x). On Humble the parameter doesn't exist; create the timer
// and cancel() it manually to get the same effect.
#if RCLCPP_VERSION_GTE(28, 0, 0)
#define JIG_HAS_TIMER_AUTOSTART 1
#else
#define JIG_HAS_TIMER_AUTOSTART 0
#endif

// Humble (rclcpp 16) rejects intraprocess comms paired with TRANSIENT_LOCAL
// durability — publishers throw std::invalid_argument("intraprocess
// communication allowed only with volatile durability") at construction.
// Iron+ (rclcpp 20+) allow the combination. Use this in QoS builder chains for
// publishers on nodes that opt into intraprocess comms; it sets transient
// local on Iron+ and falls back to the default volatile durability on Humble.
#if RCLCPP_VERSION_GTE(20, 0, 0)
#define JIG_INTRAPROCESS_TRANSIENT_LOCAL transient_local()
#else
#define JIG_INTRAPROCESS_TRANSIENT_LOCAL durability(rclcpp::DurabilityPolicy::Volatile)
#endif
