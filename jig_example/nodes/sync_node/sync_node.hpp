#include <memory>

#include <jig_example/sync_node_interface.hpp>

namespace jig_example::sync_node {

struct Session : SyncNodeSession<Session> {
    using SyncNodeSession::SyncNodeSession;
};

CallbackReturn on_configure(std::shared_ptr<Session> sn);

using SyncNode = SyncNodeBase<Session, on_configure>;

} // namespace jig_example::sync_node
