cmake_minimum_required(VERSION 3.22)
project(jig_example)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

find_package(jig REQUIRED)

# Automatically handle all package setup
jig_auto_package()

if(BUILD_TESTING)
    find_package(launch_testing_ament_cmake REQUIRED)

    # APPEND_ENV adds the test/ dir to PYTHONPATH so launch tests can import helpers.py. This is needed because
    # add_launch_test runs from the build dir, not the source dir.
    set(_test_helpers "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/test")

    add_launch_test(test/test_lifecycle.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_pub_sub.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_services.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_actions.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_timers.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_parameters.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_cross_language.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_for_each_param.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_qos_handlers.py APPEND_ENV ${_test_helpers})
    add_launch_test(test/test_tf.py APPEND_ENV ${_test_helpers})
endif()
