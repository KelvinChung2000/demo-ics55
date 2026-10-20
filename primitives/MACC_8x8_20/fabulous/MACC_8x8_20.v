// Copyright 2026 FABulous Contributors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

(* FABulous, BelMap,
A_REG=0,
B_REG=1,
C_REG=2,
SIGN_EXT=3,
ACC_SEL=4,
ACC_OUT=5,
CLK_INV=6
*)
module MACC_8x8_20 #(
    parameter NoConfigBits = 7
)(
    // Fabric side
    input  CLK,
    input  EN,

    input  ACC_RST,
    input  ACC_CI,
    output ACC_CO,
    
    input  [ 7:0] A,
    input  [ 7:0] B,
    input  [19:0] C,
    
    output [19:0] Q,

    // Static configuration bits
    (* FABulous, GLOBAL *) input [NoConfigBits-1:0] ConfigBits
);
    // Configuration bits
    wire A_REG, B_REG, C_REG, MULTIPLY, SIGN_EXT, ACC_SEL, ACC_OUT, CLK_INV;

    assign A_REG = ConfigBits[0];
    assign B_REG = ConfigBits[1];
    assign C_REG = ConfigBits[2];
    assign SIGN_EXT = ConfigBits[3];
    assign ACC_SEL = ConfigBits[4];
    assign ACC_OUT = ConfigBits[5];
    assign CLK_INV = ConfigBits[6];

    // Clock inversion, then one buffer for all 56 registers. Left to ABC the
    // inversion drives them itself from an AOI21X0P5, 1.4 ns late against the
    // fabric's other flops, which fails hold on every path into this BEL.
    wire clk_sel, clk;
    assign clk_sel = CLK_INV ? !CLK : CLK;
    clk_buf clk_drive (.A(clk_sel), .X(clk));

    // ICS55 has no enabled flop, so every `if (EN)` becomes a feedback mux
    // reading both EN and its complement. Left whole, ABC drove all 56 selects
    // from one INVX0P5 and the EN net from the switch-matrix mux, 6 ns edges
    // at the slow corner; one copy per register group keeps each under 20.
    wire en_a, en_b, en_c, en_acc, acc_rst;
    fanout_buf en_a_drive (.A(EN), .X(en_a));
    fanout_buf en_b_drive (.A(EN), .X(en_b));
    fanout_buf en_c_drive (.A(EN), .X(en_c));
    fanout_buf en_acc_drive (.A(EN), .X(en_acc));
    fanout_buf acc_rst_drive (.A(ACC_RST), .X(acc_rst));

    // Registers the inputs
    logic [7:0] A_q, B_q;
    logic [19:0] C_q;

    always_ff @(posedge clk) begin
        if (en_a) A_q <= A;
        if (en_b) B_q <= B;
        if (en_c) C_q <= C;
    end
    
    // Select the operands
    logic [7:0] OPA, OPB;
    logic [19:0] OPC;
    
    assign OPA = A_REG ? A_q : A;
    assign OPB = B_REG ? B_q : B;
    assign OPC = C_REG ? C_q : C;
    
    // Multiplication
    wire [15:0] product;
    assign product = OPA * OPB;
    
    // Sign extension
    wire [19:0] extended;
    assign extended = SIGN_EXT ? {{4{product[15]}}, product} : {4'd0, product};

    // Addition
    wire [19:0] sum;

    // Accumulator
    logic [19:0] ACC;
    always_ff @(posedge clk) begin
        if (acc_rst) begin
            ACC <= '0;
        end else begin
            if (en_acc) begin
                ACC <= sum;
            end
        end
    end

    assign {ACC_CO, sum} = extended + (ACC_SEL ? ACC : OPC) + ACC_CI;

    // Output
    assign Q = ACC_OUT ? ACC : sum;

endmodule
