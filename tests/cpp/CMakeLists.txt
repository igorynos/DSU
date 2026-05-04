include(FetchContent)
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.5.3
)
FetchContent_MakeAvailable(Catch2)

add_executable(dsu_native_tests
  test_header.cpp
)
target_link_libraries(dsu_native_tests PRIVATE dsu_native_lib Catch2::Catch2WithMain)
add_test(NAME dsu_native_tests COMMAND dsu_native_tests)
