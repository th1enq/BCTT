cmake_minimum_required(VERSION 3.20)
project(temporal_path_counting VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(TPCOUNT_NATIVE "Enable -march=native for benchmark builds" OFF)

add_library(tpcount_lib
    src/temporal_graph.cpp
    src/solvers.cpp
    src/dag.cpp
    src/ttsp.cpp
    src/tw_dp.cpp
)
target_include_directories(tpcount_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_compile_options(tpcount_lib PRIVATE -Wall -Wextra -Wpedantic)
if(TPCOUNT_NATIVE)
    target_compile_options(tpcount_lib PRIVATE -march=native)
endif()

add_executable(tpcount src/main.cpp)
target_link_libraries(tpcount PRIVATE tpcount_lib)

include(CTest)
if(BUILD_TESTING)
    add_executable(tpcount_tests tests/test_core.cpp)
    target_link_libraries(tpcount_tests PRIVATE tpcount_lib)
    target_compile_definitions(tpcount_tests PRIVATE TPCOUNT_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
    add_test(NAME tpcount_core COMMAND tpcount_tests)
    add_executable(tpcount_exhaustive tests/exhaustive.cpp)
    target_link_libraries(tpcount_exhaustive PRIVATE tpcount_lib)
endif()
