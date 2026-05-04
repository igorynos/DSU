pybind11_add_module(dsu_native
  bindings.cpp
  firmware/header.cpp
  firmware/packet.cpp
)

target_include_directories(dsu_native PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

install(TARGETS dsu_native LIBRARY DESTINATION .)

add_library(dsu_native_lib STATIC
  firmware/header.cpp
  firmware/packet.cpp
)
target_include_directories(dsu_native_lib PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)
set_target_properties(dsu_native_lib PROPERTIES POSITION_INDEPENDENT_CODE ON)
