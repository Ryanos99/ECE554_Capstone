`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/25/2026 11:14:38 AM
// Design Name: 
// Module Name: mlp_classifier_tb
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


module mlp_classifier_tb();

    
    logic             clk; 
    logic             rst_n;
    logic [43:0][7:0] movenet_data;         // Movenet points from dpu
    logic             movenet_data_valid;   // Movenet points valid
    logic [2:0]       pose_class;           // 000: Push-Up Top, 001: Push-up Bottom                                        
                                            // 010: Squat Top,   011: Squat Botto                                        
                                            // 100: Curl Top,    101: Curl Bottom
    logic             done_pulse;           // High when inference finishes

    mlp_classifier mlp(.clk(clk), .rst_n(rst_n), .movenet_data(movenet_data), .movenet_data_valid(movenet_data_valid), .pose_class(pose_class), .done_pulse(done_pulse));

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;

        // Initialize movenet data
        movenet_data[0] = 8'd0;
        movenet_data[1] = 8'd1;
        movenet_data[2] = 8'd2;
        movenet_data[3] = 8'd3;
        movenet_data[4] = 8'd4;
        movenet_data[5] = 8'd5;
        movenet_data[6] = 8'd6;
        movenet_data[7] = 8'd7;
        movenet_data[8] = 8'd8;
        movenet_data[9] = 8'd9;
        movenet_data[10] = 8'd10;
        movenet_data[11] = 8'd11;
        movenet_data[12] = 8'd12;
        movenet_data[13] = 8'd13;
        movenet_data[14] = 8'd14;
        movenet_data[15] = 8'd15;
        movenet_data[16] = 8'd16;
        movenet_data[17] = 8'd17;
        movenet_data[18] = 8'd18;
        movenet_data[19] = 8'd19;
        movenet_data[20] = 8'd20;
        movenet_data[21] = 8'd21;
        movenet_data[22] = 8'd22;
        movenet_data[23] = 8'd23;
        movenet_data[24] = 8'd24;
        movenet_data[25] = 8'd25;
        movenet_data[26] = 8'd26;
        movenet_data[27] = 8'd27;
        movenet_data[28] = 8'd28;
        movenet_data[29] = 8'd29;
        movenet_data[30] = 8'd30;
        movenet_data[31] = 8'd31;
        movenet_data[32] = 8'd32;
        movenet_data[33] = 8'd33;
        movenet_data[34] = 8'd34;
        movenet_data[35] = 8'd35;
        movenet_data[36] = 8'd36;
        movenet_data[37] = 8'd37;
        movenet_data[38] = 8'd38;
        movenet_data[39] = 8'd39;
        movenet_data[40] = 8'd40;
        movenet_data[41] = 8'd41;
        movenet_data[42] = 8'd42;
        movenet_data[43] = 8'd43;

        @(negedge clk);
        rst_n = 1'b1;
        movenet_data_valid = 'b1;

        @(negedge clk);
        movenet_data_valid = 1'b0;

        repeat(120000) @(posedge clk);
        //repeat(800) @(posedge clk);
        $stop();
        
    end

    always
        #5 clk = ~clk;

endmodule
