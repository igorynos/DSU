#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "dsu_native/api.hpp"

namespace py = pybind11;

PYBIND11_MODULE(dsu_native, m) {
    m.doc() = "DSU native module — firmware parsing and packet generation";
    m.attr("__version__")  = "2.0.0";
    m.attr("HEADER_SIZE")  = static_cast<int>(dsu::HEADER_SIZE);
    m.attr("BLOCK_SIZE")   = static_cast<int>(dsu::BLOCK_SIZE);
    m.attr("CMD_FW_INFO")  = dsu::CMD_FW_INFO;
    m.attr("CMD_FW_PACK")  = dsu::CMD_FW_PACK;

    py::class_<dsu::FirmwareHeader>(m, "FirmwareHeader")
        .def_readonly("crypt_mode",    &dsu::FirmwareHeader::crypt_mode)
        .def_readonly("device_header", &dsu::FirmwareHeader::device_header)
        .def_readonly("fw_ver",        &dsu::FirmwareHeader::fw_ver)
        .def_readonly("pcb_ver",       &dsu::FirmwareHeader::pcb_ver)
        .def_readonly("btldr_ver",     &dsu::FirmwareHeader::btldr_ver)
        .def_readonly("offset",        &dsu::FirmwareHeader::offset)
        .def_readonly("fw_len",        &dsu::FirmwareHeader::fw_len)
        .def_readonly("check_sum",     &dsu::FirmwareHeader::check_sum)
        .def_property_readonly("raw", [](const dsu::FirmwareHeader& h) {
            return py::bytes(reinterpret_cast<const char*>(h.raw.data()),
                             h.raw.size());
        });

    py::class_<dsu::FirmwareLoader>(m, "FirmwareLoader")
        .def(py::init<const std::string&>(), py::arg("path"))
        .def("is_valid", &dsu::FirmwareLoader::is_valid)
        .def("size",     &dsu::FirmwareLoader::size)
        .def("reset",    &dsu::FirmwareLoader::reset)
        .def("progress", &dsu::FirmwareLoader::progress)
        .def_property_readonly("header",
                               &dsu::FirmwareLoader::header,
                               py::return_value_policy::reference_internal)
        .def("next_packet", [](dsu::FirmwareLoader& self) -> py::object {
            auto pkt = self.next_packet();
            if (!pkt) return py::none();
            // Return (cmd:int, data:bytes) — simple, immutable, copy-safe.
            return py::make_tuple(
                static_cast<int>(pkt->cmd),
                py::bytes(reinterpret_cast<const char*>(pkt->data.data()),
                          pkt->data.size()));
        });
}
