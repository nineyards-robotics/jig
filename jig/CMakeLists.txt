cmake_minimum_required(VERSION 3.22)
project(jig)

find_package(ament_cmake_auto REQUIRED)
ament_auto_find_build_dependencies()

# Install the code generation script
install(PROGRAMS scripts/generate_node_interface.py DESTINATION lib/${PROJECT_NAME})

# Install the templates directory
install(DIRECTORY scripts/templates DESTINATION lib/${PROJECT_NAME})

# Install and export the CMake modules install(FILES cmake/jig_codegen.cmake cmake/jig_auto_package.cmake DESTINATION
# share/${PROJECT_NAME}/cmake)
install(FILES cmake/jig_auto_package.cmake cmake/jig_auto_interface_package.cmake
        DESTINATION share/${PROJECT_NAME}/cmake
)

# Export the CMake modules so other packages can use them
list(APPEND ${PROJECT_NAME}_CONFIG_EXTRAS cmake/jig_auto_package.cmake cmake/jig_auto_interface_package.cmake)

ament_python_install_package(${PROJECT_NAME})

# Install type stubs for third-party packages missing type information (e.g. C extensions)
install(DIRECTORY stubs/tf2_py-stubs DESTINATION ${PYTHON_INSTALL_DIR})

if(BUILD_TESTING)
    find_package(ament_cmake_pytest REQUIRED)
    ament_add_pytest_test(test_generate_node_interface tests/test_generate_node_interface.py TIMEOUT 300)
endif()

ament_auto_package(USE_SCOPED_HEADER_INSTALL_DIR INSTALL_TO_SHARE schemas)
