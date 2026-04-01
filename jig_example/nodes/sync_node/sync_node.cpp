#include "sync_node.hpp"

#include <memory>
#include <string>

#include "geometry_msgs/msg/point_stamped.hpp"
#include "std_msgs/msg/string.hpp"

namespace jig_example::sync_node {

void synced_callback(
    std::shared_ptr<Session> sn,
    geometry_msgs::msg::PointStamped::ConstSharedPtr a,
    geometry_msgs::msg::PointStamped::ConstSharedPtr b
) {
    auto out = std_msgs::msg::String();
    out.data = "synced: a=(" + std::to_string(a->point.x) + "," + std::to_string(a->point.y) + ") b=(" +
               std::to_string(b->point.x) + "," + std::to_string(b->point.y) + ")";
    sn->publishers.output->publish(out);
}

CallbackReturn on_configure(std::shared_ptr<Session> sn) {
    sn->subscribers.synced_points.set_callback(synced_callback);
    return CallbackReturn::SUCCESS;
}

} // namespace jig_example::sync_node
