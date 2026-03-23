// auto-generated DO NOT EDIT

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <example_interfaces/action/fibonacci.hpp>
#include <jig/base_node.hpp>
#include <jig/context.hpp>
#include <jig/action_server.hpp>

namespace test_package::action_node {

template <typename ContextType> struct ActionNodePublishers {};

template <typename ContextType> struct ActionNodeSubscribers {};

template <typename ContextType> struct ActionNodeServices {};

template <typename ContextType> struct ActionNodeServiceClients {};

template <typename ContextType> struct ActionNodeActions {
    std::shared_ptr<jig::SingleGoalActionServer<example_interfaces::action::Fibonacci>> fibonacci;
    std::shared_ptr<jig::SingleGoalActionServer<example_interfaces::action::Fibonacci>> math_compute;
};

template <typename DerivedContextType> struct ActionNodeContext : jig::Context {
    ActionNodePublishers<DerivedContextType> publishers;
    ActionNodeSubscribers<DerivedContextType> subscribers;
    ActionNodeServices<DerivedContextType> services;
    ActionNodeServiceClients<DerivedContextType> service_clients;
    ActionNodeActions<DerivedContextType> actions;
};


template <
    typename ContextType,
    auto init_func,
    auto extend_options = [](rclcpp::NodeOptions options) { return options; }>
class ActionNodeBase : public jig::BaseNode<"action_node", extend_options> {
  public:
    explicit ActionNodeBase(const rclcpp::NodeOptions &options) : jig::BaseNode<"action_node", extend_options>(options) {
        static_assert(
            std::is_base_of_v<ActionNodeContext<ContextType>, ContextType>, "ContextType must be a child of ActionNodeContext"
        );

        // init context
        auto ctx = std::make_shared<ContextType>();
        ctx->node = this->node_;
        // init actions
        ctx->actions.fibonacci = jig::create_single_goal_action_server<example_interfaces::action::Fibonacci>(ctx, "fibonacci");
        ctx->actions.math_compute = jig::create_single_goal_action_server<example_interfaces::action::Fibonacci>(ctx, "/math/compute");
        init_func(ctx);
    }
};

} // namespace test_package::action_node
