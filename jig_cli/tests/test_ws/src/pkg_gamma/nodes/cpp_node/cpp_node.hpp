#include <memory>

#include <pkg_gamma/cpp_node_interface.hpp>

namespace pkg_gamma::cpp_node {

struct Session : CppNodeSession<Session> {
    using CppNodeSession::CppNodeSession;
};

CallbackReturn on_configure(std::shared_ptr<Session> sn);

using CppNode = CppNodeBase<Session, on_configure>;

} // namespace pkg_gamma::cpp_node
