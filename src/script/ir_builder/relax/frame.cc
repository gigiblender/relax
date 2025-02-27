/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

#include <tvm/relax/expr.h>
#include <tvm/script/ir_builder/relax/frame.h>
#include <tvm/script/ir_builder/relax/ir.h>

#include "./utils.h"

namespace tvm {
namespace script {
namespace ir_builder {
namespace relax {

void SeqExprFrameNode::ExitWithScope() {
  // At this moment, there should be at most one BlockFrame which hasn't ended. In this case, call
  // its `ExitBlockFrame` and check if there is any more unended BlockFrame.
  if (Optional<BlockFrame> block_frame = IRBuilder::Current()->FindFrame<BlockFrame>()) {
    block_frame.value()->ExitWithScope();
    ICHECK(!IRBuilder::Current()->FindFrame<BlockFrame>().defined())
        << "ValueError: There is some remaining BlockFrame that is not properly popped out.";
  }
  RelaxFrameNode::ExitWithScope();
}

void FunctionFrameNode::ExitWithScope() {
  using ir::IRModuleFrame;
  using tvm::relax::Expr;
  SeqExprFrameNode::ExitWithScope();
  IRBuilder builder = IRBuilder::Current();
  // Step 1: Create the function.
  CHECK(output.defined()) << "ValueError: A Relax function must have a return value. Please use "
                             "`return` to return an Expr";
  output = this->block_builder->Normalize(output.value());
  Expr body = this->block_builder->Normalize(tvm::relax::SeqExpr(binding_blocks, output.value()));
  tvm::relax::Function func(/*params=*/params,
                            /*body=*/body,
                            /*ret_type=*/ret_type.value_or(Type()),
                            /*ret_shape=*/tvm::relax::RuntimeDepShape(),
                            /*attrs=*/DictAttrs(attrs));
  // TODO(relax-team): remove this line
  func = WithAttr(func, "global_symbol", name.value());
  // Step 2: Update IRModule.
  if (builder->frames.empty()) {
    // Case 0. No outer frame, return function directly
    ICHECK(!builder->result.defined()) << "ValueError: Builder.result has already been set";
    builder->result = func;
  } else if (Optional<IRModuleFrame> opt_frame = builder->FindFrame<IRModuleFrame>()) {
    // Case 1. A global function of an IRModule
    CHECK(name.defined()) << "ValueError: The function name must be defined before exiting the "
                             "function scope, if it's defined in a Module";
    const IRModuleFrame& frame = opt_frame.value();
    const String& func_name = name.value_or("");
    if (!frame->global_var_map.count(func_name)) {
      // First time visiting the function.
      ir::DeclFunction(func_name);
    }
    // Define the function.
    // Note we do checks to disallow redefinition of functions inside the `DefFunction`.
    ir::DefFunction(func_name, func);
  } else {
    LOG(FATAL) << "ValueError: Cannot find where to insert Relax.Function";
  }
}

void BlockFrameNode::EnterWithScope() {
  // Step 1. If the last frame is a block frame. The start of a new block frame marks the end of the
  // last block frame.
  Optional<BlockFrame> block_frame = IRBuilder::Current()->GetLastFrame<BlockFrame>();
  if (block_frame.defined()) {
    block_frame.value()->ExitWithScope();
    // Block frames cannot appear consecutively.
    ICHECK(!IRBuilder::Current()->GetLastFrame<BlockFrame>());
  }
  // Step 2. Deal with the new block frame.
  RelaxFrameNode::EnterWithScope();
  Optional<FunctionFrame> func_frame = IRBuilder::Current()->FindFrame<FunctionFrame>();
  CHECK(func_frame.defined())
      << "ValueError: Cannot find FunctionFrame when creating BindingBlocks, Please ensure "
         "creating the block under Relax function scope.";
  const tvm::relax::BlockBuilder& block_builder = func_frame.value()->block_builder;
  if (is_dataflow) {
    block_builder->BeginDataflowBlock();
  } else {
    block_builder->BeginBindingBlock();
  }
}

void BlockFrameNode::ExitWithScope() {
  // Step 1. Pop the current frame out of the frame stack.
  RelaxFrameNode::ExitWithScope();

  // Step 2. Get the constructed binding block from the block builder. The block should have at
  // lease one binding - otherwise, the block is not supposed to be created.
  const tvm::relax::BlockBuilder& block_builder = GetBlockBuilder();
  tvm::relax::BindingBlock block = block_builder->EndBlock();
  CHECK(!block->bindings.empty())
      << "ValueError: A binding block should have at lease one binding.";

  // Step 3. Get the last frame from the IRBuilder frame stack.
  Optional<RelaxFrame> opt_last_frame = IRBuilder::Current()->GetLastFrame<RelaxFrame>();
  ICHECK(opt_last_frame.defined());
  RelaxFrame last_frame = opt_last_frame.value();

  // Step 4. Since we popped out any possible block frame when entering the "with" scope of the
  // current frame, the last frame cannot be a block frame.
  ICHECK(!last_frame->IsInstance<BlockFrameNode>());

  // Step 5. Push the block frame into the corresponding field of the last frame.
  if (const auto* seq_frame = last_frame.as<SeqExprFrameNode>()) {
    ICHECK(!seq_frame->output.defined())
        << "The function is not expected to have output values when emitting blocks.";
    auto frame = GetRef<SeqExprFrame>(seq_frame);
    frame->binding_blocks.push_back(block);
  } else {
    LOG(FATAL) << "ValueError: Currently the last frame is supposed to be either a function frame "
                  "or a block frame. However, the last frame is \""
               << last_frame->GetTypeKey() << "\".";
    // TODO(ruihang): support IfFrame and then IfFrame is a possible branch here.
  }
}

void IfFrameNode::EnterWithScope() {
  const Array<IRBuilderFrame>& frames = IRBuilder::Current()->frames;
  for (const IRBuilderFrame& frame : frames) {
    const auto* block_frame = frame.as<BlockFrameNode>();
    if (block_frame && block_frame->is_dataflow) {
      LOG(FATAL) << "ValueError: Cannot create an IfFrame inside a dataflow block.";
    }
  }
  RelaxFrameNode::EnterWithScope();
}

void IfFrameNode::ExitWithScope() {
  RelaxFrameNode::ExitWithScope();
  CHECK(then_expr.defined())
      << "ValueError: The body of then part is expected to be defined before exiting.";
  CHECK(then_expr.defined())
      << "ValueError: The body of else part is expected to be defined before exiting.";
  auto body = tvm::relax::If(condition, then_expr.value(), else_expr.value());
  var = Emit(body, /*is_dataflow=*/false);
  IRBuilder::Name(var_name, var);
}

void ThenFrameNode::EnterWithScope() {
  IfFrame frame = FindIfFrame("R.Then");
  CHECK(!frame->then_expr.defined())
      << "ValueError: Duplicate then branch declaration, previous one is "
      << frame->then_expr.value();
  SeqExprFrameNode::EnterWithScope();
}

void ThenFrameNode::ExitWithScope() {
  SeqExprFrameNode::ExitWithScope();
  String var_name;
  output = GetSeqExprForBranch(GetRef<ThenFrame>(this), &var_name);
  IfFrame frame = FindIfFrame("R.Then");
  frame->then_expr = output;
  frame->var_name = var_name;
}

void ElseFrameNode::EnterWithScope() {
  IfFrame frame = FindIfFrame("R.Else");
  CHECK(frame->then_expr.defined()) << "The else branch should follow then branch";
  CHECK(!frame->else_expr.defined())
      << "ValueError: Duplicate else branch declaration, previous one is "
      << frame->else_expr.value();
  SeqExprFrameNode::EnterWithScope();
}

void ElseFrameNode::ExitWithScope() {
  SeqExprFrameNode::ExitWithScope();
  String var_name;
  output = GetSeqExprForBranch(GetRef<ElseFrame>(this), &var_name);
  IfFrame frame = FindIfFrame("R.Else");
  frame->else_expr = output;
  CHECK(frame->var_name == var_name)
      << "This last binding of both branches must have the same variable.";
}

TVM_REGISTER_NODE_TYPE(FunctionFrameNode);
TVM_REGISTER_NODE_TYPE(SeqExprFrameNode);
TVM_REGISTER_NODE_TYPE(BlockFrameNode);
TVM_REGISTER_NODE_TYPE(IfFrameNode);
TVM_REGISTER_NODE_TYPE(ThenFrameNode);
TVM_REGISTER_NODE_TYPE(ElseFrameNode);

}  // namespace relax
}  // namespace ir_builder
}  // namespace script
}  // namespace tvm
