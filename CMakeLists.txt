cmake_minimum_required(VERSION 3.18)

project(wformat)

include(FetchContent)
find_package(Python REQUIRED COMPONENTS Interpreter)

FetchContent_Declare(
    uncrustify
    GIT_REPOSITORY https://github.com/uncrustify/uncrustify.git
    GIT_TAG uncrustify-0.81.0
    GIT_SHALLOW TRUE
    GIT_PROGRESS TRUE
)
FetchContent_MakeAvailable(uncrustify)

# MinGW: link libgcc/libstdc++/winpthread statically
if(MINGW)
    message(STATUS "Warning Using MinGW")
    target_link_options(uncrustify PRIVATE -static-libgcc -static-libstdc++)
endif()

set_target_properties(
    uncrustify
    PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY $<1:${CMAKE_SOURCE_DIR}/src/wformat/bin>
)

add_custom_target(
    clang_format
    ALL
    COMMAND ${Python_EXECUTABLE} -m pip install --upgrade clang-format==20.1.8 --target ${CMAKE_BINARY_DIR}/_deps/clang-format-build
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_BINARY_DIR}/_deps/clang-format-build/clang_format/data/bin
    ${CMAKE_SOURCE_DIR}/src/wformat/bin
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Installing clang-format via pip"
    VERBATIM
)

add_custom_target(
    install_python_deps
    ALL
    COMMAND ${Python_EXECUTABLE} -m pip install --upgrade ".[build,test]"
    COMMAND ${Python_EXECUTABLE} -m pip install -e ".[build,test]" # installs a .pth that points to ./src, make it editable
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Installing Python dependencies via pip"
    VERBATIM
)

add_custom_target(
    python_project_setup
    COMMENT "Setup Python Project properly for development and extension build"
    VERBATIM
)

add_dependencies(python_project_setup install_python_deps clang_format uncrustify)

add_custom_target(
    pyinstaller_bundle
    ALL
    COMMAND ${Python_EXECUTABLE} -m PyInstaller -y wformat.spec
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Building wformat executable with PyInstaller"
    VERBATIM
)

add_custom_target(
    pyinstaller_bundle_for_vs
    ALL
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_SOURCE_DIR}/dist/wformat
    ${CMAKE_SOURCE_DIR}/extensions/vs/dist/wformat
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Copying PyInstaller output to VS extension folder"
    VERBATIM
)

add_dependencies(pyinstaller_bundle python_project_setup)
add_dependencies(pyinstaller_bundle_for_vs pyinstaller_bundle)
