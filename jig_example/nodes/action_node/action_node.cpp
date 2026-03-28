#include "action_node.hpp"

#include <memory>
#include <rclcpp/logging.hpp>
#include <vector>

#include "example_interfaces/action/fibonacci.hpp"

#include <jig/timer.hpp>

using namespace std::chrono_literals;
using Fibonacci = example_interfaces::action::Fibonacci;

namespace jig_example::action_node {

void process_goal(
    std::shared_ptr<jig::SingleGoalActionServer<Fibonacci>> action_server, std::shared_ptr<Session> /*sn*/
) {
    auto goal = action_server->get_active_goal();
    if (!goal) {
        return;
    }

    // Compute full Fibonacci sequence
    std::vector<int32_t> sequence;
    sequence.push_back(0);
    if (goal->order > 0) {
        sequence.push_back(1);
    }
    for (int32_t i = 2; i < goal->order; ++i) {
        sequence.push_back(sequence[i - 1] + sequence[i - 2]);
    }

    // Publish feedback with partial sequence
    auto feedback = std::make_shared<Fibonacci::Feedback>();
    feedback->sequence = sequence;
    action_server->publish_feedback(feedback);

    // Succeed with final result
    auto result = std::make_shared<Fibonacci::Result>();
    result->sequence = sequence;
    action_server->succeed(result);
}

CallbackReturn on_configure(std::shared_ptr<Session> sn) {
    // compute: single goal, rejects invalid orders, no replacement
    sn->actions.compute->set_options({
        .new_goals_replace_current_goal = false,
        .goal_validator = [](const Fibonacci::Goal &goal) -> bool { return goal.order >= 0; },
    });

    // compute_replace: allows goal replacement
    sn->actions.compute_replace->set_options({
        .new_goals_replace_current_goal = true,
        .goal_validator = [](const Fibonacci::Goal &goal) -> bool { return goal.order >= 0; },
    });

    // Timer to process active goals every 100ms
    jig::create_timer(sn, 100ms, [](std::shared_ptr<Session> sn) {
        process_goal(sn->actions.compute, sn);
        process_goal(sn->actions.compute_replace, sn);
    });

    return CallbackReturn::SUCCESS;
}

} // namespace jig_example::action_node
