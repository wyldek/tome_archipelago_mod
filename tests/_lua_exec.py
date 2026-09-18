"""Execute Lua assertions with Lupa or a local Lua 5.4 library.

The fallback uses the real Lua VM, not a Python reimplementation. It exists for
restricted development environments; release validation still requires Lupa so
the original Lupa-backed tests cannot silently skip.
"""
from __future__ import annotations
import ctypes
import ctypes.util


class LuaExecutor:
    def __init__(self):
        self.vm = None
        self.state = None
        try:
            import lupa
        except ImportError:
            path = ctypes.util.find_library("lua5.4")
            if not path:
                raise RuntimeError("Install the test extra (Lupa); no Lua runtime is available")
            self.lib = lib = ctypes.CDLL(path)
            lib.luaL_newstate.restype = ctypes.c_void_p
            lib.luaL_openlibs.argtypes = [ctypes.c_void_p]
            lib.luaL_loadbufferx.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t,
                                           ctypes.c_char_p, ctypes.c_char_p]
            lib.luaL_loadbufferx.restype = ctypes.c_int
            lib.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_ssize_t, ctypes.c_void_p]
            lib.lua_pcallk.restype = ctypes.c_int
            lib.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
            lib.lua_tolstring.restype = ctypes.c_char_p
            lib.lua_settop.argtypes = [ctypes.c_void_p, ctypes.c_int]
            lib.lua_close.argtypes = [ctypes.c_void_p]
            self.state = lib.luaL_newstate()
            if not self.state:
                raise RuntimeError("Could not allocate a Lua state")
            lib.luaL_openlibs(self.state)
        else:
            self.vm = lupa.LuaRuntime(unpack_returned_tuples=True)
        self.execute("unpack = unpack or table.unpack")

    def execute(self, source: str):
        if self.vm is not None:
            self.vm.execute(source)
            return
        data = source.encode("utf-8")
        code = self.lib.luaL_loadbufferx(self.state, data, len(data), b"@regression", b"t")
        if not code:
            code = self.lib.lua_pcallk(self.state, 0, 0, 0, 0, None)
        if code:
            message = self.lib.lua_tolstring(self.state, -1, None)
            self.lib.lua_settop(self.state, 0)
            raise AssertionError(message.decode("utf-8", "replace") if message else "Lua failure")

    def close(self):
        if self.state:
            self.lib.lua_close(self.state)
            self.state = None
        self.vm = None
