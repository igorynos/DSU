cmake_minimum_required(VERSION 3.20)
project(dsu_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
  add_compile_options(/W4 /permissive-)
else()
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

add_subdirectory(src/dsu_native)

option(DSU_BUILD_TESTS "Build C++ tests" OFF)
if(DSU_BUILD_TESTS)
  enable_testing()
  add_subdirectory(tests/cpp)
endif()
