`default_nettype none

// Behavioural model of the fabric's MACC_8x8_20 BEL, its ConfigBits as the
// parameters FABulous's addBelsToPrim emits.
module MACC_8x8_20 (
    input wire CLK,
    input wire EN,
    input wire ACC_RST,
    input wire ACC_CI,
    output wire ACC_CO,
    input wire A0, A1, A2, A3, A4, A5, A6, A7,
    input wire B0, B1, B2, B3, B4, B5, B6, B7,
    input wire C0, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19,
    output wire Q0, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19
);
    parameter A_REG = 0;
    parameter B_REG = 0;
    parameter C_REG = 0;
    parameter SIGN_EXT = 0;
    parameter ACC_SEL = 0;
    parameter ACC_OUT = 0;
    parameter CLK_INV = 0;

    wire [7:0] A = {A7, A6, A5, A4, A3, A2, A1, A0};
    wire [7:0] B = {B7, B6, B5, B4, B3, B2, B1, B0};
    wire [19:0] C = {C19, C18, C17, C16, C15, C14, C13, C12, C11, C10, C9, C8, C7, C6, C5, C4, C3, C2, C1, C0};
    wire [19:0] Q;
    assign {Q19, Q18, Q17, Q16, Q15, Q14, Q13, Q12, Q11, Q10, Q9, Q8, Q7, Q6, Q5, Q4, Q3, Q2, Q1, Q0} = Q;

    wire clk = CLK_INV ? ~CLK : CLK;

    reg [7:0] a_q, b_q;
    reg [19:0] c_q;
    always @(posedge clk) begin
        if (EN) a_q <= A;
        if (EN) b_q <= B;
        if (EN) c_q <= C;
    end

    wire [7:0] opa = A_REG ? a_q : A;
    wire [7:0] opb = B_REG ? b_q : B;
    wire [19:0] opc = C_REG ? c_q : C;

    wire [15:0] product = opa * opb;
    wire [19:0] extended = SIGN_EXT ? {{4{product[15]}}, product} : {4'd0, product};

    reg [19:0] acc;
    wire [19:0] sum;
    always @(posedge clk)
        if (ACC_RST) acc <= 20'd0;
        else if (EN) acc <= sum;

    assign {ACC_CO, sum} = extended + (ACC_SEL ? acc : opc) + ACC_CI;
    assign Q = ACC_OUT ? acc : sum;
endmodule

`default_nettype wire
