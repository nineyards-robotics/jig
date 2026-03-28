#include <memory>

#include <jig_example/echo_node_interface.hpp>

namespace jig_example::echo_node {

struct Session : EchoNodeSession<Session> {
    using EchoNodeSession::EchoNodeSession;
    int counter = 0;
};

CallbackReturn on_configure(std::shared_ptr<Session> sn);

using EchoNode = EchoNodeBase<Session, on_configure>;

} // namespace jig_example::echo_node
