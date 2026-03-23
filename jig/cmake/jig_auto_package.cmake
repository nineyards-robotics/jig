# ============================================================================
# jig_auto_package.cmake
#
# Automated build system for ROS 2 packages with jig nodes. Expects nodes/ directory with subdirectories containing
# interface.yaml and C++ or Python implementation files.
#
# NOTE: Most internal functions are implemented as macros (not functions) for consistency with ament_cmake patterns and
# to preserve variable scope behavior. This allows macros like ament_auto_add_library() and
# rclcpp_components_register_node() to properly set variables in the caller's scope for later use by
# ament_auto_package(). All macro-local variables are prefixed with _jig_ or _jig_node_ to avoid namespace pollution.
# ============================================================================

# Detect which languages (C++ and/or Python) are present in a directory Args: DIR - Directory to scan for source files
# OUT_HAS_CPP - Output variable, set to TRUE if .cpp files found OUT_HAS_PYTHON - Output variable, set to TRUE if .py
# files found
function(_jig_detect_languages DIR OUT_HAS_CPP OUT_HAS_PYTHON)
    file(GLOB_RECURSE CPP_SOURCE_FILES "${DIR}/*.cpp")
    file(GLOB_RECURSE PY_SOURCE_FILES "${DIR}/*.py")

    set(${OUT_HAS_CPP} FALSE PARENT_SCOPE)
    set(${OUT_HAS_PYTHON} FALSE PARENT_SCOPE)

    if(CPP_SOURCE_FILES)
        set(${OUT_HAS_CPP} TRUE PARENT_SCOPE)
    endif()

    if(PY_SOURCE_FILES)
        set(${OUT_HAS_PYTHON} TRUE PARENT_SCOPE)
    endif()
endfunction()

# Convert snake_case to PascalCase (e.g., "my_node" -> "MyNode") Args: OUTPUT_VAR - Variable name to store the result
# INPUT_STRING - snake_case string to convert
function(_jig_snake_to_pascal OUTPUT_VAR INPUT_STRING)
    string(REPLACE "_" ";" WORD_LIST ${INPUT_STRING})
    set(RESULT "")

    foreach(WORD ${WORD_LIST})
        # Capitalize first letter
        string(SUBSTRING ${WORD} 0 1 FIRST_CHAR)
        string(TOUPPER ${FIRST_CHAR} FIRST_CHAR_UPPER)
        string(SUBSTRING ${WORD} 1 -1 REST)
        string(APPEND RESULT "${FIRST_CHAR_UPPER}${REST}")
    endforeach()

    set(${OUTPUT_VAR} ${RESULT} PARENT_SCOPE)
endfunction()

# Main entry point for jig build system Automates the entire build process for ROS 2 packages with jig nodes. Detects
# languages, generates interfaces, builds libraries, and registers components. Requires: nodes/ directory with at least
# one .cpp or .py file
macro(jig_auto_package)
    # Parse optional arguments
    set(_jig_auto_options "")
    set(_jig_auto_oneValueArgs "")
    set(_jig_auto_multiValueArgs "INSTALL_TO_SHARE")
    cmake_parse_arguments(
        JIG_AUTO "${_jig_auto_options}" "${_jig_auto_oneValueArgs}" "${_jig_auto_multiValueArgs}" ${ARGN}
    )

    # Auto-detect standard directories to install to share
    set(_jig_auto_detected_dirs "")
    if(IS_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/launch")
        list(APPEND _jig_auto_detected_dirs "launch")
    endif()
    if(IS_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/config")
        list(APPEND _jig_auto_detected_dirs "config")
    endif()

    # Combine auto-detected directories with user-specified ones
    set(_jig_install_to_share_combined ${_jig_auto_detected_dirs} ${JIG_AUTO_INSTALL_TO_SHARE})
    if(_jig_install_to_share_combined)
        list(REMOVE_DUPLICATES _jig_install_to_share_combined)
    endif()

    find_package(ament_cmake_auto REQUIRED)
    ament_auto_find_build_dependencies()

    # NOTE: JIG_NODES_DIR is part of the jig cmake API
    set(JIG_NODES_DIR "${CMAKE_CURRENT_SOURCE_DIR}/nodes")

    if(NOT IS_DIRECTORY ${JIG_NODES_DIR})
        message(FATAL_ERROR "jig: nodes/ directory not found at ${JIG_NODES_DIR}")
    endif()

    _jig_detect_languages(${JIG_NODES_DIR} _jig_HAS_CPP _jig_HAS_PYTHON)

    if(NOT _jig_HAS_CPP AND NOT _jig_HAS_PYTHON)
        message(FATAL_ERROR "jig: nodes/ directory has no C++ (.cpp) or Python (.py) files.")
    endif()

    if(_jig_HAS_CPP)
        # NOTE: JIG_CPP_PACKAGE_TARGET is part of the jig cmake API
        set(JIG_CPP_PACKAGE_TARGET "${PROJECT_NAME}")
        _jig_create_package_shared_cpp_library(${JIG_CPP_PACKAGE_TARGET})
    endif()

    if(_jig_HAS_PYTHON)
        # set up python package
        find_package(ament_cmake_python REQUIRED)
        _ament_cmake_python_get_python_install_dir()
        _jig_create_top_level_python_package()
    endif()

    _jig_generate_nodes(${JIG_NODES_DIR})

    # Process and install interface.yaml files with token replacement
    _jig_process_and_install_interfaces(${JIG_NODES_DIR})

    # Finalize package with scoped header install directory (best practice). USE_SCOPED_HEADER_INSTALL_DIR is used so
    # that we behave the same way on Jazzy as with Kilted. As far as I can tell, this is a non-breaking change because
    # it also changes which include directory is set with ament_export_include_directories - i.e. it doesn't really
    # matter.
    if(_jig_install_to_share_combined)
        ament_auto_package(USE_SCOPED_HEADER_INSTALL_DIR INSTALL_TO_SHARE ${_jig_install_to_share_combined})
    else()
        ament_auto_package(USE_SCOPED_HEADER_INSTALL_DIR)
    endif()
endmacro()

# Create shared C++ library for all C++ nodes Creates a shared library from all .cpp files in nodes/ directory
macro(_jig_create_package_shared_cpp_library)
    # NOTE: this uses a slightly implicit path "nodes" because ament_auto_add_library uses a relative path we have
    # already checked the nodes directory exists in jig_auto_package before calling this function
    ament_auto_add_library(${JIG_CPP_PACKAGE_TARGET} SHARED DIRECTORY nodes)
    target_compile_features(${JIG_CPP_PACKAGE_TARGET} PUBLIC cxx_std_20)
    message(STATUS "jig: Created C++ library '${JIG_CPP_PACKAGE_TARGET}'")
endmacro()

# Create top-level Python package __init__.py Generates and installs __init__.py to make package importable
macro(_jig_create_top_level_python_package)
    # Create top-level __init__.py for the package
    set(_jig_PACKAGE_INIT_PY "${CMAKE_CURRENT_BINARY_DIR}/python_package_init/__init__.py")
    file(WRITE ${_jig_PACKAGE_INIT_PY} "# Auto-generated by jig_auto_package\n")
    install(FILES ${_jig_PACKAGE_INIT_PY} DESTINATION "${PYTHON_INSTALL_DIR}/${PROJECT_NAME}")
    message(STATUS "jig: Created Python package '${PROJECT_NAME}'")
endmacro()

# Discover and process all nodes in the nodes/ directory Args: NODES_DIR - Path to nodes/ directory containing node
# subdirectories
macro(_jig_generate_nodes NODES_DIR)
    file(GLOB _jig_NODE_DIRS RELATIVE ${NODES_DIR} ${NODES_DIR}/*)
    if(NOT _jig_NODE_DIRS)
        message(WARNING "jig: No nodes found in ${NODES_DIR}")
        return()
    endif()

    message(STATUS "jig: Auto-generating nodes from ${NODES_DIR}")

    # find the generator script
    unset(_jig_codegen_script_BIN CACHE)
    find_program(
        _jig_codegen_script_BIN
        NAMES "generate_node_interface.py"
        PATHS "${jig_DIR}/../../../lib/jig"
        NO_DEFAULT_PATH
    )
    if(NOT _jig_codegen_script_BIN)
        message(FATAL_ERROR "Could not find generate_node_interface.py in ${jig_DIR}/../../../lib/jig")
    endif()

    foreach(_jig_NODE_ENTRY ${_jig_NODE_DIRS})
        set(_jig_NODE_PATH "${NODES_DIR}/${_jig_NODE_ENTRY}")
        if(IS_DIRECTORY ${_jig_NODE_PATH})
            _jig_generate_node(${_jig_NODE_ENTRY} ${_jig_NODE_PATH})
        endif()
    endforeach()
endmacro()

# Process a single node and generate language-specific interfaces Validates interface.yaml exists and dispatches to C++
# or Python generation. Mixed language nodes are not supported. Args: NODE_NAME - Name of the node NODE_DIR - Full path
# to the node's directory
macro(_jig_generate_node NODE_NAME NODE_DIR)
    set(_jig_node_INTERFACE_YAML "${NODE_DIR}/interface.yaml")
    if(NOT EXISTS ${_jig_node_INTERFACE_YAML})
        message(FATAL_ERROR "jig: Node '${NODE_NAME}' is missing interface.yaml.")
    endif()

    # Check for package == node name collision
    if("${NODE_NAME}" STREQUAL "${PROJECT_NAME}")
        message(
            FATAL_ERROR
                "jig: Node '${NODE_NAME}' has the same name as the package '${PROJECT_NAME}'. "
                "This is not allowed because:\n" "  1. It causes CMake target name conflicts (library vs executable)\n"
                "  2. It creates ambiguous C++ namespace references"
        )
    endif()

    _jig_detect_languages(${NODE_DIR} _jig_node_HAS_CPP _jig_node_HAS_PYTHON)
    if(_jig_node_HAS_CPP AND _jig_node_HAS_PYTHON)
        message(
            FATAL_ERROR
                "jig: Node '${NODE_NAME}' has both C++ and Python files. Mixed language nodes are not supported."
        )
    elseif(NOT _jig_node_HAS_CPP AND NOT _jig_node_HAS_PYTHON)
        message(FATAL_ERROR "jig: Node '${NODE_NAME}' has no C++ (.cpp) or Python (.py) files.")
    endif()

    if(_jig_node_HAS_CPP)
        _jig_generate_cpp_node(${NODE_NAME} ${_jig_node_INTERFACE_YAML})
    endif()

    if(_jig_node_HAS_PYTHON)
        _jig_generate_python_node(${NODE_NAME} ${NODE_DIR} ${_jig_node_INTERFACE_YAML})
    endif()
endmacro()

# Generate C++ interface, parameters, and component registration Creates interface header, parameter library, and
# registers as rclcpp_component. Plugin class follows pattern: ${PROJECT_NAME}::${NODE_NAME}::${NodeNamePascal} Args:
# NODE_NAME - Name of the node INTERFACE_YAML - Path to interface.yaml file
macro(_jig_generate_cpp_node NODE_NAME INTERFACE_YAML)
    find_package(rclcpp REQUIRED)
    find_package(rclcpp_components REQUIRED)
    find_package(generate_parameter_library REQUIRED)

    set(_jig_node_LIB_INCLUDE_DIR ${CMAKE_CURRENT_BINARY_DIR}/include/${PROJECT_NAME})
    file(MAKE_DIRECTORY ${_jig_node_LIB_INCLUDE_DIR})

    set(_jig_node_INTERFACE_HEADER_FILE ${_jig_node_LIB_INCLUDE_DIR}/${NODE_NAME}_interface.hpp)
    set(_jig_node_INTERFACE_PARAMS_FILE ${_jig_node_LIB_INCLUDE_DIR}/${NODE_NAME}_interface.params.yaml)
    set(_jig_node_REGISTRATION_CPP_FILE ${_jig_node_LIB_INCLUDE_DIR}/${NODE_NAME}_registration.cpp)
    set(_jig_node_INTERFACE_YAML_FILE ${_jig_node_LIB_INCLUDE_DIR}/${NODE_NAME}.yaml)

    set(
        _jig_node_CODEGEN_CMD
        ${_jig_codegen_script_BIN}
        ${INTERFACE_YAML}
        --language
        cpp
        --package
        ${PROJECT_NAME}
        --node-name
        ${NODE_NAME}
        --output
        ${_jig_node_LIB_INCLUDE_DIR}
    )

    add_custom_command(
        OUTPUT ${_jig_node_INTERFACE_HEADER_FILE} ${_jig_node_INTERFACE_PARAMS_FILE} ${_jig_node_REGISTRATION_CPP_FILE}
               ${_jig_node_INTERFACE_YAML_FILE}
        COMMAND ${_jig_node_CODEGEN_CMD}
        DEPENDS ${INTERFACE_YAML}
        DEPENDS ${_jig_codegen_script_BIN}
        COMMENT "Generating C++ interface for node '${NODE_NAME}'"
        VERBATIM
    )

    set(_jig_node_INTERFACE_LIB_NAME "${NODE_NAME}_interface")
    add_library(${_jig_node_INTERFACE_LIB_NAME} INTERFACE ${_jig_node_INTERFACE_HEADER_FILE})
    target_include_directories(
        ${_jig_node_INTERFACE_LIB_NAME} INTERFACE $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/include>
                                                  $<INSTALL_INTERFACE:include>
    )
    set_target_properties(${_jig_node_INTERFACE_LIB_NAME} PROPERTIES LINKER_LANGUAGE CXX)
    target_link_libraries(${_jig_node_INTERFACE_LIB_NAME} INTERFACE rclcpp::rclcpp rclcpp_lifecycle::rclcpp_lifecycle)

    # Install the generated headers
    install(DIRECTORY ${_jig_node_LIB_INCLUDE_DIR} DESTINATION include)

    # Export dependencies
    ament_export_dependencies(rclcpp)

    target_link_libraries(${JIG_CPP_PACKAGE_TARGET} ${_jig_node_INTERFACE_LIB_NAME})

    message(STATUS "jig: Generated C++ interface library for node '${NODE_NAME}'")

    # generate_parameter_library expects a path relative to CMAKE_CURRENT_SOURCE_DIR Compute the relative path from
    # source to binary dir
    file(RELATIVE_PATH _jig_node_INTERFACE_PARAMS_FILE_REL ${CMAKE_CURRENT_SOURCE_DIR}
         ${_jig_node_INTERFACE_PARAMS_FILE}
    )

    set(_jig_node_PARAMETERS_LIB_NAME "${NODE_NAME}_parameters")
    generate_parameter_library(${_jig_node_PARAMETERS_LIB_NAME} ${_jig_node_INTERFACE_PARAMS_FILE_REL})

    # Make parameters library depend on interface library (which generates the .params.yaml)
    add_dependencies(${_jig_node_PARAMETERS_LIB_NAME} ${_jig_node_INTERFACE_LIB_NAME})

    target_link_libraries(${JIG_CPP_PACKAGE_TARGET} ${_jig_node_PARAMETERS_LIB_NAME})
    message(STATUS "jig: Generated parameters library for node '${NODE_NAME}'")

    # Add the generated registration .cpp file to the package target
    target_sources(${JIG_CPP_PACKAGE_TARGET} PRIVATE ${_jig_node_REGISTRATION_CPP_FILE})

    # Add source directory to include path so registration file can find node headers
    target_include_directories(${JIG_CPP_PACKAGE_TARGET} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

    # Ensure the registration file is generated before compiling
    add_dependencies(${JIG_CPP_PACKAGE_TARGET} ${_jig_node_INTERFACE_LIB_NAME})

    # Register the node as an rclcpp component Convention: ${PROJECT_NAME}::${NodeNamePascal}
    _jig_snake_to_pascal(_jig_node_CLASS_NAME ${NODE_NAME})
    set(_jig_node_PLUGIN_CLASS "${PROJECT_NAME}::${_jig_node_CLASS_NAME}")

    rclcpp_components_register_node(${JIG_CPP_PACKAGE_TARGET} PLUGIN ${_jig_node_PLUGIN_CLASS} EXECUTABLE ${NODE_NAME})
    message(STATUS "jig: Registered component '${_jig_node_PLUGIN_CLASS}' with executable '${NODE_NAME}'")

    # Install the generated interface YAML file
    install(FILES ${_jig_node_INTERFACE_YAML_FILE} DESTINATION share/${PROJECT_NAME}/interfaces)
endmacro()

# Generate Python interface and executable wrapper Creates _interface.py, _parameters.py, and executable using
# runpy.run_module(). Installs to ${PYTHON_INSTALL_DIR}/${PROJECT_NAME}/${NODE_NAME}/ Args: NODE_NAME - Name of the node
# NODE_DIR - Full path to node directory INTERFACE_YAML - Path to interface.yaml file
macro(_jig_generate_python_node NODE_NAME NODE_DIR INTERFACE_YAML)
    set(_jig_node_PYTHON_GEN_DIR ${CMAKE_CURRENT_BINARY_DIR}/python_generated/${NODE_NAME})
    file(MAKE_DIRECTORY ${_jig_node_PYTHON_GEN_DIR})

    # Generated files
    set(_jig_node_INTERFACE_PY ${_jig_node_PYTHON_GEN_DIR}/interface.py)
    set(_jig_node_PARAMETERS_INTERNAL_PY ${_jig_node_PYTHON_GEN_DIR}/_parameters.py)
    set(_jig_node_PARAMETERS_PY ${_jig_node_PYTHON_GEN_DIR}/parameters.py)
    set(_jig_node_INIT_PY ${_jig_node_PYTHON_GEN_DIR}/__init__.py)
    set(_jig_node_INTERFACE_YAML_FILE ${_jig_node_PYTHON_GEN_DIR}/${NODE_NAME}.yaml)

    set(
        _jig_node_CODEGEN_CMD
        ${_jig_codegen_script_BIN}
        ${INTERFACE_YAML}
        --language
        python
        --package
        ${PROJECT_NAME}
        --node-name
        ${NODE_NAME}
        --output
        ${_jig_node_PYTHON_GEN_DIR}
    )

    add_custom_command(
        OUTPUT ${_jig_node_INTERFACE_PY} ${_jig_node_PARAMETERS_INTERNAL_PY} ${_jig_node_PARAMETERS_PY}
               ${_jig_node_INIT_PY} ${_jig_node_INTERFACE_YAML_FILE}
        COMMAND ${_jig_node_CODEGEN_CMD}
        DEPENDS ${INTERFACE_YAML}
        DEPENDS ${_jig_codegen_script_BIN}
        COMMENT "Generating Python interface for node '${NODE_NAME}'"
        VERBATIM
    )

    add_custom_target(
        ${NODE_NAME}_interface ALL
        DEPENDS ${_jig_node_INTERFACE_PY} ${_jig_node_PARAMETERS_INTERNAL_PY} ${_jig_node_PARAMETERS_PY}
                ${_jig_node_INIT_PY} ${_jig_node_INTERFACE_YAML_FILE}
    )

    # Install user Python files to site-packages/${PROJECT_NAME}/${NODE_NAME}/
    file(GLOB _jig_node_USER_PY_FILES "${NODE_DIR}/*.py")
    if(_jig_node_USER_PY_FILES)
        install(FILES ${_jig_node_USER_PY_FILES} DESTINATION "${PYTHON_INSTALL_DIR}/${PROJECT_NAME}/${NODE_NAME}")
        message(STATUS "jig: Installed user Python files for node '${NODE_NAME}'")
    endif()

    # Install generated Python interface files to site-packages/${PROJECT_NAME}/${NODE_NAME}/
    install(
        DIRECTORY ${_jig_node_PYTHON_GEN_DIR}/
        DESTINATION "${PYTHON_INSTALL_DIR}/${PROJECT_NAME}/${NODE_NAME}"
        FILES_MATCHING
        PATTERN "*.py"
    )

    # Generate wrapper executable using runpy.run_module()
    set(_jig_node_EXECUTABLE_PATH "${CMAKE_CURRENT_BINARY_DIR}/executables/${NODE_NAME}")
    file(
        WRITE ${_jig_node_EXECUTABLE_PATH}
        "#!/usr/bin/env python3
import runpy

# Run the node's main file as __main__
runpy.run_module('${PROJECT_NAME}.${NODE_NAME}.${NODE_NAME}', run_name='__main__')
"
    )

    # Make executable
    file(
        CHMOD
        ${_jig_node_EXECUTABLE_PATH}
        PERMISSIONS
        OWNER_READ
        OWNER_WRITE
        OWNER_EXECUTE
        GROUP_READ
        GROUP_EXECUTE
        WORLD_READ
        WORLD_EXECUTE
    )

    # Install executable to lib/${PROJECT_NAME}/ for ros2 run
    install(PROGRAMS ${_jig_node_EXECUTABLE_PATH} DESTINATION lib/${PROJECT_NAME})

    # Install the generated interface YAML file
    install(FILES ${_jig_node_INTERFACE_YAML_FILE} DESTINATION share/${PROJECT_NAME}/interfaces)
endmacro()

# Process and install top-level interface.yaml files from optional interfaces/ directory. Per-node interface.yaml files
# are now processed and installed by the code generation script. Args: NODES_DIR - Path to nodes/ directory containing
# node subdirectories
macro(_jig_process_and_install_interfaces NODES_DIR)
    set(_jig_interfaces_output_dir "${CMAKE_CURRENT_BINARY_DIR}/interfaces")
    file(MAKE_DIRECTORY ${_jig_interfaces_output_dir})

    # Collect expected generated node YAML names (for conflict checking)
    set(_jig_generated_node_yaml_names "")
    file(GLOB _jig_interface_NODE_DIRS RELATIVE ${NODES_DIR} ${NODES_DIR}/*)
    foreach(_jig_interface_NODE_ENTRY ${_jig_interface_NODE_DIRS})
        set(_jig_interface_NODE_PATH "${NODES_DIR}/${_jig_interface_NODE_ENTRY}")
        if(IS_DIRECTORY ${_jig_interface_NODE_PATH})
            set(_jig_interface_YAML_PATH "${_jig_interface_NODE_PATH}/interface.yaml")
            if(EXISTS ${_jig_interface_YAML_PATH})
                list(APPEND _jig_generated_node_yaml_names "${_jig_interface_NODE_ENTRY}.yaml")
            endif()
        endif()
    endforeach()

    # Process top-level interfaces/ directory if it exists
    set(_jig_toplevel_interfaces_dir "${CMAKE_CURRENT_SOURCE_DIR}/interfaces")
    set(_jig_interfaces_files_to_install "")
    if(IS_DIRECTORY ${_jig_toplevel_interfaces_dir})
        file(GLOB _jig_toplevel_interface_files "${_jig_toplevel_interfaces_dir}/*.yaml")

        foreach(_jig_toplevel_interface_file ${_jig_toplevel_interface_files})
            get_filename_component(_jig_interface_filename ${_jig_toplevel_interface_file} NAME)

            # Check for naming conflicts with generated node YAML files
            list(FIND _jig_generated_node_yaml_names "${_jig_interface_filename}" _jig_conflict_index)
            if(NOT _jig_conflict_index EQUAL -1)
                message(
                    FATAL_ERROR
                        "jig: Naming conflict detected! Package-level interfaces/${_jig_interface_filename} conflicts with auto-generated interface YAML for a node. Please rename the package-level file."
                )
            endif()

            # Copy the file to the build directory
            set(_jig_interface_output_file "${_jig_interfaces_output_dir}/${_jig_interface_filename}")
            configure_file(${_jig_toplevel_interface_file} ${_jig_interface_output_file} COPYONLY)

            list(APPEND _jig_interfaces_files_to_install ${_jig_interface_output_file})

            message(STATUS "jig: Processed package-level interfaces/${_jig_interface_filename}")
        endforeach()
    endif()

    # Install top-level interface files
    if(_jig_interfaces_files_to_install)
        list(LENGTH _jig_interfaces_files_to_install _jig_interfaces_count)
        install(FILES ${_jig_interfaces_files_to_install} DESTINATION share/${PROJECT_NAME}/interfaces)
        message(
            STATUS
                "jig: Installing ${_jig_interfaces_count} package-level interface files to share/${PROJECT_NAME}/interfaces/"
        )
    endif()
endmacro()
