pybind11_add_module(dsu_native
  bindings.cpp
)

target_include_directories(dsu_native PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

install(TARGETS dsu_native LIBRARY DESTINATION .)
