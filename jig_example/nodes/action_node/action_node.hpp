#include <memory>

#include <jig_example/action_node_interface.hpp>

namespace jig_example::action_node {

struct Session : ActionNodeSession<Session> {
    using ActionNodeSession::ActionNodeSession;
};

CallbackReturn on_configure(std::shared_ptr<Session> sn);

using ActionNode = ActionNodeBase<Session, on_configure>;

} // namespace jig_example::action_node
