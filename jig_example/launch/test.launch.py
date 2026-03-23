import clingwrap as cw


def generate_launch_description():
    l = cw.LaunchBuilder()

    with l.namespace("cleaning"):
        l.node("jig_example", "my_node")
        l.node("jig_example", "python_node")

    return l
