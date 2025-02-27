# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Package tvm.script.ir_builder.ir.ir"""

from tvm.ir import BaseFunc, GlobalVar

from . import _ffi_api
from .frame import IRModuleFrame


def ir_module() -> IRModuleFrame:
    """Start a ir_module frame.
    Returns
    -------
    frame: IRModuleFrame
        The constructed frame.
    """
    return _ffi_api.IRModule()  # type: ignore[attr-defined] # pylint: disable=no-member


def decl_function(func_name: str) -> GlobalVar:
    """Declare a Function without given the specific function implementation.
    Parameters
    ----------
    func_name : str
        The function unique name.
    Note
    ----
    It is usually used in cross-function call. And we can specify the function by `DefFunction`
    Returns
    -------
    gv : GlobalVar
        The corresponding GlobalVar.
    """
    return _ffi_api.DeclFunction(func_name)  # pylint: disable=no-member # type: ignore


def def_function(func_name: str, func: BaseFunc) -> None:
    """Define the function which is declared before.
    Parameters
    ----------
    func_name : str
        The function unique name.
    func: BaseFunc
        The given function implementation
    """
    return _ffi_api.DefFunction(func_name, func)  # pylint: disable=no-member # type: ignore
