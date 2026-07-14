"""PyInstaller runtime hook: make OpenTelemetry entry_points discoverable."""

import sys as _sys

# Marker: verify this hook actually runs
try:
    with open(r"D:\Dev\repos\temp\hook_ran_marker.txt", "w") as _f:
        _f.write("runtime-opentelemetry.py executed at " + str(_sys.argv))
except Exception:
    pass

# opentelemetry uses from opentelemetry.util._importlib_metadata import entry_points
# which re-exports from the third-party importlib_metadata (not stdlib importlib.metadata).
# Patch both.

import importlib.metadata as _md

try:
    import importlib_metadata as _im
except ImportError:
    _im = None

_ENTRIES: dict[str, dict[str, str]] = {
    "opentelemetry_context": {
        "contextvars_context": "opentelemetry.context.contextvars_context:ContextVarsRuntimeContext",
    },
    "opentelemetry_environment_variables": {
        "api": "opentelemetry.environment_variables",
    },
    "opentelemetry_meter_provider": {
        "default_meter_provider": "opentelemetry.metrics:NoOpMeterProvider",
    },
    "opentelemetry_propagator": {
        "baggage": "opentelemetry.baggage.propagation:W3CBaggagePropagator",
        "tracecontext": "opentelemetry.trace.propagation.tracecontext:TraceContextTextMapPropagator",
    },
    "opentelemetry_tracer_provider": {
        "default_tracer_provider": "opentelemetry.trace:NoOpTracerProvider",
    },
}


class _FakeEntryPoint:
    def __init__(self, name, module_path):
        self.name = name
        self.value = module_path
        self.group = ""

    def load(self):
        module_name, attr_name = self.value.split(":", 1)
        mod = __import__(module_name, fromlist=[attr_name])
        return getattr(mod, attr_name)


def _make_patcher(_mod):
    if _mod is None:
        return
    _orig = _mod.entry_points

    def _patched(**kw):
        group, name = kw.get("group"), kw.get("name")
        if group in _ENTRIES:
            entries = _ENTRIES[group]
            if name is not None:
                if name in entries:
                    return iter([_FakeEntryPoint(name, entries[name])])
                return iter([])
            return iter([_FakeEntryPoint(n, p) for n, p in entries.items()])
        return _orig(**kw)

    _mod.entry_points = _patched


_make_patcher(_md)
_make_patcher(_im)
