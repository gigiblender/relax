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
# pylint: disable=invalid-name
"""Relax transformation passes."""
import functools
import inspect
import types
from typing import Callable, Dict, List, Optional, Union

import numpy as np
import tvm.ir
from tvm.runtime import NDArray
from . import _ffi_api


@tvm._ffi.register_object("relax.FunctionPass")
class FunctionPass(tvm.ir.transform.Pass):
    """A pass that works on each tvm.relax.Function in a module. A function
    pass class should be created through `function_pass`.
    """


@tvm._ffi.register_object("relax.DataflowBlockPass")
class DataflowBlockPass(tvm.ir.transform.Pass):
    """A pass that works on each tvm.relax.DataflowBlock in a module."""


def FailTestRewrite() -> tvm.ir.transform.Pass:
    """Incorrectly transform the dataflow structure as fail testcases.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.FailTestRewrite()


def RewriteFMA() -> tvm.ir.transform.Pass:
    """Perform fused multiply add rewriting in dataflow blocks.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.RewriteFMA()


def FuseFMA() -> tvm.ir.transform.Pass:
    """Perform fused multiply add rewriting, generate a subgraph(sub function),
    and call into the sub function in the main function.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.FuseFMA()


def LambdaLift():
    """
    Lift local functions into global.

    Returns
    -------
    ret : tvm.ir.transform.Pass
    """
    return _ffi_api.LambdaLift()


def ToNonDataflow() -> tvm.ir.transform.Pass:
    """Transform all dataflow structure to non-dataflow version.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.ToNonDataflow()


def CallTIRRewrite() -> tvm.ir.transform.Pass:
    """Perform explicit tensor allocation for call_tir.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.CallTIRRewrite()


def VMMemoryLower() -> tvm.ir.transform.Pass:
    """Perform memory lowering. Lowers the relax.builtin.alloc_tensor intrinsic to VM intrinsics.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.VMMemoryLower()


def VMShapeLower() -> tvm.ir.transform.Pass:
    """Lower the shape expressions in relax to VM shape heap manipulations and generate related
    TIR functions to do shape calculations.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.VMShapeLower()


def Normalize() -> tvm.ir.transform.Pass:
    """Transforming Relax IR to normal form, i.e., the expressions are normalized(no nesting
    and hence the AST is in ANF), and all checked_type_ and shape_ of expressions are available.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.Normalize()


def CanonicalizeBindings() -> tvm.ir.transform.Pass:
    """
    Canonicalizes variable definitions
    (e.g., if there is y = x and z = y, it replaces uses of y and z with x).

    Best combined with constant folding and the elimination of unused definitions.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.CanonicalizeBindings()


def ResolveGlobals() -> tvm.ir.transform.Pass:
    """Resolve global variables using string equality. This ensures all GlobalVars in the IR refer
    to the correct GlobalVar of the input IRModule. An error is reported if any GlobalVar cannot be
    resolved.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.ResolveGlobals()


def BindParams(
    func_name: str,
    params: Dict[str, Union[tvm.runtime.NDArray, np.ndarray]],
) -> tvm.ir.transform.Pass:
    """Bind params of function of the module to constant tensors.

    Parameters
    ----------

    func_name: str
        The function name to be bound

    params : Dict[str, Union[tvm.runtime.NDArray, np.ndarray]]
        The map from param name to constant tensors.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    tvm_params = {}
    for k, v in params.items():
        if isinstance(v, np.ndarray):
            v = tvm.nd.array(v)
        assert isinstance(
            v, tvm.runtime.NDArray
        ), f"param values are expected to be TVM.NDArray or numpy.ndarray, but got {type(v)}"
        tvm_params[k] = v

    return _ffi_api.BindParams(func_name, tvm_params)


def RemoveUnusedFunctions(entry_functions: Optional[List[str]] = None) -> tvm.ir.transform.Pass:
    """Remove unused relax/prim functions without external linkage in a IRModule.

    Parameters
    ----------
    entry_functions: Optional[List[str]]
        The set of entry functions to start from.

    Returns
    -------
    ret : tvm.transform.Pass
        The registered pass to remove unused functions.
    """
    if entry_functions is None:
        entry_functions = ["main"]
    return _ffi_api.RemoveUnusedFunctions(entry_functions)


def RunCodegen(
    target_codegens: Optional[List[str]] = None, entry_functions: Optional[List[str]] = None
) -> tvm.ir.transform.Pass:
    """Produce the runtime::Module with an annotated codegen and global symbol.

    Parameters
    ----------
    target_codegens: Optional[List[str]]
        List of target codegens. If empty, perform all codegens by default.
    entry_functions: Optional[List[str]]
        The set of entry functions to start from.

    Returns
    -------
    ret : tvm.transform.Pass
        The registered pass to remove unused functions.
    """
    if entry_functions is None:
        entry_functions = ["main"]
    return _ffi_api.RunCodegen(target_codegens, entry_functions)


def FoldConstant() -> tvm.ir.transform.Pass:
    """Fold constant expressions.

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.FoldConstant()


def AnnotateTIROpPattern() -> tvm.ir.transform.Pass:
    """Annotate Op Pattern Kind for TIR functions

    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.AnnotateTIROpPattern()


def FuseOps(fuse_opt_level=-1) -> tvm.ir.transform.Pass:
    """This pass groups bindings in a dataflow block of Relax functions and generate a new grouped
    Relax function for each group, according to the fusion algorithm described in the pass
    implementation. By grouping bindings into new Relax functions, we substitute the bindings in
    the function being manipulated into function calls to the new grouped function.

    A follow-up pass named "FuseTIR" will generate a TIR PrimFunc for each grouped function.

    Parameters
    ----------
    fuse_opt_level : int
        The level of fuse optimization. -1 indicates that the level will be
        inferred from pass context.

    Returns
    -------
    ret : tvm.transform.Pass
        The registered pass for operator fusion.
    """
    return _ffi_api.FuseOps(fuse_opt_level)


def FuseTIR() -> tvm.ir.transform.Pass:
    """Fuse primitive relax function into a larger TIR function if possible

    Returns
    -------
    ret : tvm.transform.Pass
        The registered pass for tir fusion.
    """
    return _ffi_api.FuseTIR()


def MetaScheduleApplyDatabase(
    work_dir: Optional[str] = None,
) -> tvm.ir.transform.Pass:
    """Apply the best schedule from tuning database.
    work_dir : Optional[str]
       work directory to deduce default database if database is not provided
       (it will be ignored when an user passes database)
    Returns
    -------
    ret : tvm.transform.Pass
        The registered pass
    """
    return _ffi_api.MetaScheduleApplyDatabase(work_dir)


def MetaScheduleTuneTIR(
    work_dir: str,
    max_trials_global: int,
) -> tvm.ir.transform.Pass:
    """Tune TIR with MetaSchedule.
    Parameters
    ----------
    work_dir: str
       work directory
    max_trials_gloabl: int
       maximum number of total trials allowed for tuning
    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.MetaScheduleTuneTIR(work_dir, max_trials_global)


def MetaScheduleTuneIRMod(
    params: Dict[str, NDArray],
    work_dir: str,
    max_trials_global: int,
) -> tvm.ir.transform.Pass:
    """Tune Relax IRModule with MetaSchedule.
    Parameters
    ----------
    params: Dict[str, NDArray]
       model params
    work_dir: str
       work directory
    max_trials_gloabl: int
       maximum number of total trials allowed for tuning
    Returns
    -------
    ret: tvm.ir.transform.Pass
    """
    return _ffi_api.MetaScheduleTuneIRMod(params, work_dir, max_trials_global)


def _wrap_class_function_pass(pass_cls, pass_info):
    """Wrap a python class as function pass."""

    class PyFunctionPass(FunctionPass):
        """Internal wrapper class to create a class instance."""

        def __init__(self, *args, **kwargs):
            # initialize handle in case pass_cls creation failed.
            self.handle = None
            inst = pass_cls(*args, **kwargs)

            # it is important not to capture self to
            # avoid a cyclic dependency
            def _pass_func(func, mod, ctx):
                return inst.transform_function(func, mod, ctx)

            self.__init_handle_by_constructor__(_ffi_api.MakeFunctionPass, _pass_func, pass_info)
            self._inst = inst

        def __getattr__(self, name):
            # fall back to instance attribute if there is not any
            return self._inst.__getattribute__(name)

    functools.update_wrapper(PyFunctionPass.__init__, pass_cls.__init__)
    PyFunctionPass.__name__ = pass_cls.__name__
    PyFunctionPass.__doc__ = pass_cls.__doc__
    PyFunctionPass.__module__ = pass_cls.__module__
    return PyFunctionPass


def function_pass(
    pass_func=None,
    opt_level=None,
    name=None,
    required=None,
    traceable=False,
) -> Union[Callable, FunctionPass]:
    """Decorate a function pass.

    This function returns a callback when pass_func
    is provided. Otherwise, it returns the created function pass using the
    given optimization function.

    Parameters
    ----------
    pass_func : Optional[Callable[(Function, Module, PassContext) -> Function]]
        The transformation function or class.

    opt_level : int
        The optimization level of this function pass.

    name : Optional[str]
        The name of the function pass. The name could be empty. In this case, the
        name of the optimization function will be used as the pass name.

    required : Optional[List[str]]
        The list of passes that the function pass is dependent on.

    traceable: Boolean
        Boolean variable whether the function pass is traceable

    Returns
    -------
    create_function_pass : Union[Callable, FunctionPass]

        A decorator will be returned if pass_func is not provided,
        otherwise return the decorated result.
        The returned decorator has two behaviors depending on the input:
        A new FunctionPass will be returned when we decorate a pass function.
        A new FunctionPass class will be returned when we decorate a class type.

    Examples
    --------
    The following code block decorates a function pass class.

    .. code-block:: python

        @relax.transform.function_pass(opt_level=1)
        class TestReplaceFunc:
            def __init__(self, new_func):
                self.new_func = new_func

            def transform_function(self, func, mod, ctx):
                # just for demo purposes
                # transform func to new_func
                return self.new_func

        @R.function
        def f1(x: Tensor[(m, n), "float32"]):
            return x

        @tvm.script.ir_module
        class InputMod:
            @R.function
            def f2(x: Tensor[(m, n), "float32"]):
                gv0 = relax.add(x, x)
                return gv0
        # fpass is now a special pass that replaces every
        # function to f1
        fpass = TestReplaceFunc(f1)
        # now every function in InputMod is replaced by f1
        updated_mod = fpass(InputMod)


    The following code creates a function pass by decorating
    a user defined transform function.

    .. code-block:: python

        @relax.transform.function_pass(opt_level=2)
        def transform(func, mod, ctx):
            # my transformations here.
            return func

        function_pass = transform
        assert isinstance(function_pass, relax.transform.FunctionPass)
        assert function_pass.info.opt_level == 2

        # Given a module m, the optimization could be invoked as the follwoing:
        updated_mod = function_pass(m)
        # Now transform should have been applied to every function in
        # the provided module m. And the updated module will be returned.
    """

    if opt_level is None:
        raise ValueError("Please provide opt_level for the function pass.")

    required = required if required else []
    if not isinstance(required, (list, tuple)):
        raise TypeError("Required is expected to be the type of " + "list/tuple.")

    def create_function_pass(pass_arg):
        """Internal function that creates a function pass"""
        fname = name if name else pass_arg.__name__
        info = tvm.transform.PassInfo(opt_level, fname, required, traceable)
        if inspect.isclass(pass_arg):
            return _wrap_class_function_pass(pass_arg, info)
        if not isinstance(pass_arg, (types.FunctionType, types.LambdaType)):
            raise TypeError("pass_func must be a callable for Function pass")
        return _ffi_api.MakeFunctionPass(pass_arg, info)

    if pass_func:
        return create_function_pass(pass_func)
    return create_function_pass


def _wrap_class_dataflowblock_pass(pass_cls, pass_info):
    """Wrap a python class as dataflowblock pass"""

    class PyDataflowBlockPass(DataflowBlockPass):
        """Internal wrapper class to create a class instance."""

        def __init__(self, *args, **kwargs):
            # initialize handle in case pass_cls creation failed.
            self.handle = None
            inst = pass_cls(*args, **kwargs)

            # it is important not to capture self to
            # avoid a cyclic dependency
            def _pass_func(func, mod, ctx):
                return inst.transform_dataflowblock(func, mod, ctx)

            self.__init_handle_by_constructor__(
                _ffi_api.MakeDataflowBlockPass, _pass_func, pass_info
            )
            self._inst = inst

        def __getattr__(self, name):
            # fall back to instance attribute if there is not any
            return self._inst.__getattribute__(name)

    functools.update_wrapper(PyDataflowBlockPass.__init__, pass_cls.__init__)
    PyDataflowBlockPass.__name__ = pass_cls.__name__
    PyDataflowBlockPass.__doc__ = pass_cls.__doc__
    PyDataflowBlockPass.__module__ = pass_cls.__module__
    return PyDataflowBlockPass


def dataflowblock_pass(
    pass_func=None, opt_level=None, name=None, required=None, traceable=False
) -> Union[Callable, DataflowBlockPass]:
    """Decorate a dataflowblock pass.

    This function returns a callback when pass_func
    is provided. Otherwise, it returns the created dataflowblock pass using the
    given optimization function.

    Parameters
    ----------
    pass_func : Optional[Callable[(DataflowBlock, Module, PassContext) -> DataflowBlock]]
        The transformation function or class.

    opt_level : int
        The optimization level of this dataflowblock pass.

    name : Optional[str]
        The name of the dataflowblock pass. The name could be empty. In this case, the
        name of the optimization function will be used as the pass name.

    required : Optional[List[str]]
        The list of passes that the dataflowblock pass is dependent on.

    traceable: Boolean
        Boolean variable whether the dataflowblock pass is traceable

    Returns
    -------
    create_dataflowblock_pass : Union[Callable, DataflowBlockPass]

        A decorator will be returned if pass_func is not provided,
        otherwise return the decorated result.
        The returned decorator has two behaviors depending on the input:
        A new DataflowBlockPass will be returned when we decorate a pass function.
        A new DataflowBlockPass class will be returned when we decorate a class type.

    Examples
    --------
    The following code block decorates a dataflowblock pass class.

    .. code-block:: python

        @relax.transform.dataflowblock_pass(opt_level=1)
        class TestReplaceBinding:
            # Simple test function to replace the first VarBinding to another.

            def __init__(self):
                # create a new VarBinding
                m, n = tir.Var("m", "int64"), tir.Var("n", "int64")
                type_anno = relax.DynTensorType(2, "float32")
                lv0 = relax.Var("lv1", [m, n], type_anno)
                val = relax.const(np.random.rand(24, 56))
                self.new_binding = relax.VarBinding(lv0, val)

            def transform_dataflowblock(self, block, mod, ctx):
                # just for demo purposes
                # Replace the first binding in the DataflowBlock
                new_bindings = [self.new_binding, block.bindings[1]]
                new_block = relax.expr.DataflowBlock(new_bindings, block.span)
                return new_block

        @tvm.script.ir_module
        class InputMod:
            @R.function
            def f1(x: Tensor[(m, n), "float32"]):
                with relax.dataflow():
                    lv0 = relax.multiply(x, x)
                    gv0 = relax.add(x, x)
                    relax.output(gv0)
                return gv0
        # block_pass is now a special pass that replaces every
        # first binding to the constant value binding
        block_pass = TestReplaceBinding()
        # now every first binding in DataflowBlock of InputMod
        # is replaced by new_binding
        updated_mod = block_pass(InputMod)


    The following code creates a dataflowblock pass by decorating
    a user defined transform function.

    .. code-block:: python

        @relax.transform.dataflowblock_pass(opt_level=2)
        def transform(block, mod, ctx):
            # my transformations here.
            return block

        block_pass = transform
        assert isinstance(block_pass, relax.transform.DataflowBlockPass)
        assert block_pass.info.opt_level == 2

        # Given a module m, the optimization could be invoked as the follwoing:
        updated_mod = block_pass(m)
        # Now transform should have been applied to every DataflowBlock in
        # the provided module m. And the updated module will be returned.
    """

    if opt_level is None:
        raise ValueError("Please provide opt_level for the dataflowblock pass.")

    required = required if required else []
    if not isinstance(required, (list, tuple)):
        raise TypeError("Required is expected to be the type of " + "list/tuple.")

    def create_dataflowblock_pass(pass_arg):
        """Internal function that creates a dataflowblock pass"""
        fname = name if name else pass_arg.__name__
        info = tvm.transform.PassInfo(opt_level, fname, required, traceable)
        if inspect.isclass(pass_arg):
            return _wrap_class_dataflowblock_pass(pass_arg, info)
        if not isinstance(pass_arg, (types.FunctionType, types.LambdaType)):
            raise TypeError("pass_func must be a callable for DataflowBlock pass")
        return _ffi_api.MakeDataflowBlockPass(pass_arg, info)

    if pass_func:
        return create_dataflowblock_pass(pass_func)
    return create_dataflowblock_pass
