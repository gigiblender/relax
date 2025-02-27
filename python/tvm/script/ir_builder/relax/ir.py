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
# pylint: disable=redefined-builtin, wrong-import-order
"""IRBuilder for Relax dialect"""

from typing import Dict, List, Optional, Tuple, Union

from tvm._ffi import register_object as _register_object
from tvm.ir import Attrs, Type
from tvm.relax import Call, Expr, ExternFunc, ShapeExpr, Var

############################### Operators ###############################
from tvm.relax.op import (
    add,
    builtin,
    call_tir,
    invoke_closure,
    make_closure,
    multiply,
    print,
    shape_of,
    unique,
)
from tvm.relax.ty import ObjectType, ShapeType
from tvm.runtime import Object as tvm_Object
from tvm.tir import PrimExpr

from ..tir import var as _tir_var
from . import _ffi_api, frame

############################## Tensor Type ##############################


@_register_object("script.ir_builder.relax.TensorType")
class TensorType(tvm_Object):
    """A temporary Tensor type for `R.Tensor` in ir_builder."""


def tensor(
    shape: Optional[List[Union[PrimExpr, str]]] = None,
    dtype: Optional[str] = None,
    ndim: int = -1,
):
    """Helper function for `R.Tensor` in parser
    Parameters
    ----------
    shape: Optional[List[Union[PrimExpr, str]]]
        The shape of the tensor. It's runtime dependent if `shape` is None.
    dtype: Optional[str]
        The element data type of the tensor. It's runtime dependent if `dtype` is None.
    ndim: int
        The number of dimensions of the tensor. It's runtime dependent if `ndim` is -1.
    Returns
    -------
    tensor_type: TensorType
        The TensorType that is only used in ir_builder.
    """

    if shape is not None:
        if not isinstance(shape, list):
            shape = list(shape)

        for i, s in enumerate(shape):
            if isinstance(s, str):
                shape[i] = _tir_var("int64", s)

    return _ffi_api.Tensor(shape, dtype, ndim)  # pylint: disable=no-member # type: ignore


############################## Other Types ##############################

Object = ObjectType()  # pylint: disable=invalid-name
Shape = ShapeType()  # pylint: disable=invalid-name

############################### Function ################################


def function() -> frame.FunctionFrame:
    """Start a function frame.
    Returns
    -------
    frame: FunctionFrame
        The constructed function frame.
    """
    return _ffi_api.Function()  # pylint: disable=no-member # type: ignore


def arg(name: str, type: Union[Type, TensorType], shape: Optional[ShapeExpr] = None) -> Var:
    """Add a parameter to the last function frame.
    Parameters
    ----------
    name: str
        The name of the parameter.
    type: Union[Type, TensorType]
        The type of the parameter. It can be a typical TVM Type or a TensorType,
        which contains both type and shape
    shape: Optional[ShapeExpr]
        The shape of the parameter.
    Returns
    -------
    var: Var
        The created function parameter var.
    """

    if isinstance(type, TensorType):
        if shape is not None:
            raise ValueError("Cannot specify the shape if we use TensorType")
        shape = type.shape
        type = type.type

    return _ffi_api.Arg(name, type, shape)  # pylint: disable=no-member # type: ignore


def func_name(name: str) -> None:
    """Specify the name of the last function frame.
    Parameters
    ----------
    name: str
        The function name.
    """
    return _ffi_api.FuncName(name)  # pylint: disable=no-member # type: ignore


def func_attr(attrs: Dict[str, tvm_Object]) -> None:
    """Specify the attrs of the last function frame.
    Parameters
    ----------
    attrs: Dict[str, Object]
        The function attrs.
    """
    return _ffi_api.FuncAttrs(attrs)  # pylint: disable=no-member # type: ignore


def func_ret_type(ret_type: Union[TensorType, Type]) -> None:
    """Specify the return type of the last function frame.
    Parameters
    ----------
    ret_type: Union[TensorType, Type]
        The function return type.
    """
    if isinstance(ret_type, TensorType):
        ret_type = ret_type.type
    return _ffi_api.FuncRetType(ret_type)  # pylint: disable=no-member # type: ignore


def func_ret_value(value: Expr) -> None:
    """Specify the return value of the last function frame.
    Parameters
    ----------
    value: Expr
        The function return value.
    """
    return _ffi_api.FuncRetValue(value)  # pylint: disable=no-member # type: ignore


############################# BindingBlock ##############################


def dataflow() -> frame.BlockFrame:
    """Start a dataflow binding block frame.
    Returns
    -------
    frame: frame.BlockFrame
        The created ir_builder Block frame.
    """
    return _ffi_api.Dataflow()  # pylint: disable=no-member # type: ignore


def output(*vars: Tuple[Var]) -> Tuple[Var]:
    """Expose the dataflow block output variables as global ones.
    Parameters
    ----------
    vars: Tuple[Var]
        The output variables of a dataflow block.
    Returns
    -------
    vars: Tuple[Var]
        The output variables of a dataflow block. Return the input variables to parser side for
        followup process
    """
    _ffi_api.DataflowBlockOutput(vars)  # pylint: disable=no-member # type: ignore
    return vars


################################## Ops #################################


def call_packed(
    func: str,
    *args: List[Expr],
    attrs: Optional[Attrs] = None,
    type_args: Optional[Union[TensorType, List[TensorType]]] = None,
) -> Call:
    """Create a relax Call, which calls a packed function.
    Parameters
    ----------
    func: str
        The name of extern function.
    args : List[Expr]
        The arguments.
    attrs: Optional[Attrs]
        The call attributes
    type_args: Optional[Union[TensorType, List[TensorType]]]
        List of Types
    Returns
    -------
    call: Call
        The created Relax Call
    """
    op = ExternFunc(func)
    if type_args is None:
        raise ValueError(f"R.call_packed is required to have type_args")
    if isinstance(type_args, (TensorType, Type)):
        type_args = [type_args]
    elif isinstance(type_args, tuple):
        type_args = list(type_args)
    for i, argument in enumerate(type_args):
        if isinstance(argument, TensorType):
            type_args[i] = argument.type
        elif isinstance(argument, Type):
            type_args[i] = argument
        else:
            raise TypeError(
                "call_packed `type_args` is expected to be list of TensorType/Type, "
                f"but got {type(arg)}"
            )

    return Call(op, args, attrs=attrs, type_args=type_args)


############################### Bindings ###############################


def emit(value: Expr, is_dataflow_var: bool) -> Var:
    """Emit a binding to the last binding block frame.
    Parameters
    ----------
    value: Expr
        The right side value of the bindings to be emitted.
    is_dataflow_var: bool
        A boolean indicating if the emitted binding variable is a dataflow variable.
    Returns
    -------
    var: Var
        The left side var of the emitted binding.
    """
    return _ffi_api.Emit(value, is_dataflow_var)  # pylint: disable=no-member # type: ignore


def emit_match_shape(
    value: Expr, pattern: List[PrimExpr], emit_var: bool, is_dataflow_var: bool
) -> Optional[Var]:
    """Emit a match_shape binding to the last binding block frame.
    Parameters
    ----------
    value: Expr
        The value of the MatchShape to be emitted.
    pattern: List[PrimExpr]
        The pattern of the MatchShape to be emitted.
    emit_var: bool
        A boolean indicating if the MatchShape contains the emitted variable.
    is_dataflow_var: bool
        A boolean indicating if the emitted variable is a dataflow variable when `emit_var` is True.
        When `emit_var` is False, the value of this flag will be ignored.
    Returns
    -------
    var: Optional[Var]
        The emitted var if `emit_var` is True. Otherwise, return `None`.
    """
    return _ffi_api.EmitMatchShape(value, pattern, emit_var, is_dataflow_var)  # type: ignore


############################# Type Deduce ##############################


def annotate_type_shape(var: Var, anno_type: Type, anno_shape: ShapeExpr) -> None:
    """Annotate and check the type of relax var.
    Parameters
    ----------
    var: Var
        The input var to be annotated.

    anno_type: Type
        The annotated type

    anno_shape: ShapeExpr
        The annotated shape

    """
    _ffi_api.AnnotateTypeShape(var, anno_type, anno_shape)


def If(condition: Expr) -> frame.IfFrame:  # pylint: disable=invalid-name
    """Create an if frame.
    Parameters
    ----------
    condition : Expr
        The condition of if statement, executes the true branch if the condition is true,
        otherwise jump into the false branch.
    Returns
    -------
    res : frame.IfFrame
        The result IfFrame.
    """
    return _ffi_api.If(condition)  # pylint: disable=no-member # type: ignore


def Then() -> frame.ThenFrame:  # pylint: disable=invalid-name
    """Create a then frame.
    Returns
    -------
    res : frame.ThenFrame
        The result ThenFrame.
    """
    return _ffi_api.Then()  # pylint: disable=no-member # type: ignore


def Else() -> frame.ElseFrame:  # pylint: disable=invalid-name
    """Create an else frame.
    Returns
    -------
    res : frame.ElseFrame
        The result ElseFrame.
    """
    return _ffi_api.Else()  # pylint: disable=no-member # type: ignore


############################### Importer ###############################

__all__ = [
    "Else",
    "If",
    "Object",
    "Shape",
    "TensorType",
    "Then",
    "add",
    "arg",
    "builtin",
    "call_packed",
    "call_tir",
    "dataflow",
    "emit",
    "emit_match_shape",
    "func_attr",
    "func_name",
    "func_ret_type",
    "func_ret_value",
    "function",
    "invoke_closure",
    "make_closure",
    "multiply",
    "output",
    "print",
    "unique",
    "shape_of",
    "tensor",
]
