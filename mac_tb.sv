`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/22/2026 08:57:32 PM
// Design Name: 
// Module Name: mac_tb
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module mac_tb();

    
    logic               clk;
    logic               valid_mac_inputs;
    logic signed [7:0]  point;        // move net point 
    logic signed [7:0]  weight;       // Weight from BRAM
    logic signed [19:0] acc_in;       // Previous accumulation sum
    logic signed [20:0] acc_out;      // Updated sum
    logic               valid_mac_out;

    mac mac_inst(.clk(clk), .valid_mac_inputs(valid_mac_inputs), .point(point), .weight(weight), .acc_in(acc_in), .acc_out(acc_out), .valid_mac_out(valid_mac_out));

    initial begin
        clk = 1'b0;

        valid_mac_inputs = 1'b1;
        point = 8'd1;
        weight = 8'd1;
        acc_in = 19'd0;

        @(posedge clk);
        point = 8'd2;
        weight = 8'd2;
        //acc_in = 19'd1;
        acc_in = 19'd0;

        @(posedge clk);
        valid_mac_inputs = 1'b0;
        point = 8'd3;
        weight = 8'd3;
        //acc_in = 19'd5;
        acc_in = 19'd0;

        @(posedge clk);
        @(posedge clk);
        valid_mac_inputs = 1'b1;
        acc_in = 19'd1;

        @(posedge clk);
        valid_mac_inputs = 1'b0;
        acc_in           = 19'd14;

        repeat(5) @(posedge clk);
        $stop();
    end

    always
        #5 clk = ~clk;
endmodule
