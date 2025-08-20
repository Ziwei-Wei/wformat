cmake_minimum_required(VERSION 3.18)

project(rd-format)

include(FetchContent)
find_package(Python REQUIRED COMPONENTS Interpreter)

# Fetch uncrustify
FetchContent_Declare(
    uncrustify
    GIT_REPOSITORY https://github.com/uncrustify/uncrustify.git
    GIT_TAG uncrustify-0.81.0
    GIT_SHALLOW TRUE
    GIT_PROGRESS TRUE
)
FetchContent_MakeAvailable(uncrustify)

set_target_properties(
    uncrustify
    PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Fetch clang-format
add_custom_target(
    clang_format 
    ALL
    COMMAND ${Python_EXECUTABLE} -m pip install --upgrade clang-format==20.1.8 --target ${CMAKE_BINARY_DIR}/_deps/clang-format-build
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_BINARY_DIR}/_deps/clang-format-build/clang_format/data/bin
    ${CMAKE_BINARY_DIR}/bin
    COMMENT "Installing clang-format via pip"
    VERBATIM
)

# pip automatically looks for a pyproject.toml (PEP 517/518) in the current working directory (. in this case).
add_custom_target(
    install_python_deps
    ALL
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_BINARY_DIR}/bin
    ${CMAKE_SOURCE_DIR}/src/rd_format/bin
    COMMAND ${Python_EXECUTABLE} -m pip install --upgrade .
    COMMAND ${Python_EXECUTABLE} -m pip install -e .  # installs a .pth that points to ./src, make it editable
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Installing Python dependencies via pip"
)

# use PyInstaller to create executable for extensions to use 
add_custom_target(
    pyinstaller_bundle
    ALL
    COMMAND ${Python_EXECUTABLE} -m pyinstaller -y --clean rd-format.spec
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    DEPENDS install_python_deps
    COMMENT "Building rd-format executable with PyInstaller"
    VERBATIM
)