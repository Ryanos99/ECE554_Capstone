`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/20/2026 05:33:50 PM
// Design Name: 
// Module Name: weight_bram_ctrl_tb
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


module weight_bram_ctrl_tb();

    
    logic       clk;
    logic       rst_n;
    logic       new_addr_valid;
    logic [1:0] layer_sel;       // 00: Layer 1, 01: Layer 2, 10: Output, 11: Bias 
    logic [7:0] neuron;          // Neuron we are calculating (max neurons is 128)
    logic [6:0] input_num;       // Max is 128 inputs 
    logic [7:0] bias_sel;        // [127:0] Layer 1 biases, [191:128] Layer 2 , [196:192] Output
    logic       weight_data_valid;
    logic [7:0] weight_data;      // Data to MAC

    weight_bram_ctrl w_b_ctrl(.clk(clk), .rst_n(rst_n),
                              .new_addr_valid(new_addr_valid), .layer_sel(layer_sel), .neuron(neuron), .input_num(input_num), .bias_sel(bias_sel),
                              .weight_data_valid(weight_data_valid), .weight_data(weight_data));

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;

        // address should be 0x0001
        new_addr_valid = 1'b0;
        layer_sel      = 2'b00;
        neuron         = 8'd0;
        input_num      = 7'd1;
        bias_sel       = 8'd0;

        @(negedge clk);
        rst_n = 1'b1;

        @(posedge clk);
        @(negedge clk);
        new_addr_valid = 1'b1;

        @(posedge clk);

        @(posedge clk);
        new_addr_valid = 1'b0;

        // Check if data is valid and is correct number for address 0x0001
        @(negedge clk);
        if(weight_data_valid != 1'b1) begin
            $display("weight data should be valid");
        end
        if(weight_data != 8'h01) begin
            $display("weight data should be 01 for address 0x0001");
        end

        repeat(3) @(posedge clk);

        @(negedge clk);
        // address should be 0x1b00
        layer_sel      = 2'b01;
        neuron         = 8'd20;
        input_num      = 7'd0;
        new_addr_valid = 1'b1;
        
        @(posedge clk);

        @(posedge clk);
        new_addr_valid = 1'b0;

        // Check if data is valid and is correct number for address 0x1b00
        @(negedge clk);
        if(weight_data_valid != 1'b1) begin
            $display("weight data should be valid");
        end
        if(weight_data != 8'h00) begin
            $display("weight data should be 00 for address 0x1b00");
        end

        repeat(3) @(posedge clk);

        @(negedge clk);
        // address should be 0x3185
        layer_sel      = 2'b10;
        neuron         = 8'd2;
        input_num      = 7'd5;
        new_addr_valid = 1'b1;
        
        @(posedge clk);

        @(posedge clk);
        new_addr_valid = 1'b0;

        // Check if data is valid and is correct number for address 0x3185
        @(negedge clk);
        if(weight_data_valid != 1'b1) begin
            $display("weight data should be valid");
        end
        if(weight_data != 8'h85) begin
            $display("weight data should be 85 for address 0x3185");
        end
        
        repeat(3) @(posedge clk);

        @(negedge clk);
        // address should be 0x3238
        layer_sel      = 2'b11;
        bias_sel       = 8'd120;
        new_addr_valid = 1'b1;
        
        @(posedge clk);

        @(posedge clk);
        new_addr_valid = 1'b0;

        // Check if data is valid and is correct number for address 0x3238
        @(negedge clk);
        if(weight_data_valid != 1'b1) begin
            $display("weight data should be valid");
        end
        if(weight_data != 8'h38) begin
            $display("weight data should be 38 for address 0x3238");
        end

        repeat(5) @(posedge clk);
        $stop();

    end

    always
        #5 clk = ~clk;

endmodule
