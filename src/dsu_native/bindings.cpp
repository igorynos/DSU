#include <pybind11/pybind11.h>

namespace py = pybind11;

PYBIND11_MODULE(dsu_native, m) {
    m.doc() = "DSU native module — firmware parsing and packet generation";
    m.attr("__version__") = "2.0.0";
}
