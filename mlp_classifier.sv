`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 03/22/2026 09:53:14 PM
// Design Name: 
// Module Name: mlp_classifier
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


module mlp_classifier(
        input  logic             clk, 
        input  logic             rst_n,
        input  logic [33:0][7:0] movenet_data,         // Movenet points from dpu
        input  logic             movenet_data_valid,   // Movenet points valid
        output logic [1:0]       pose_class,           // 00: Push-Up, 01: Squat, 10: Curl, 11: No pose
        output logic             done_pulse  // High when inference finishes
    );


    
    /////////////////////////
    // LOGIC INSTANTATIONS //
    /////////////////////////

    // State machine signals
    typedef enum reg [4:0] {IDLE, LAYER1_BIAS, LAYER1_INPUTS, LAYER1_MAC, LAYER1_WAIT_MAC, LAYER1_NEURON,
                                  LAYER2_BIAS, LAYER2_INPUTS, LAYER2_MAC, LAYER2_WAIT_MAC, LAYER2_NEURON,
                                  OUTPUT_BIAS, OUTPUT_INPUTS, OUTPUT_MAC, OUTPUT_WAIT_MAC, OUTPUT_NEURON, DONE} state_t;
    state_t state, next_state;

    // Weight BRAM input signals
    logic       new_addr_valid;
    logic [1:0] layer_sel;          // 00 - Layer 1, 01 - Layer 2, 10 - Output, 11 - Bias
    logic [6:0] neuron;
    logic [6:0] input_num;          // Max is 128 inputs 
    logic [7:0] bias_sel;           // [127:0] Layer 1 biases, [191:128] Layer 2 , [196:192] Output

    // Weight BRAM output signals
    logic       weight_data_valid;
    logic [7:0] weight_data;

    // MAC inputs and outputs
    logic               valid_mac_inputs;
    logic signed [7:0]  point;              // move net point 
    logic signed [7:0]  weight;             // Weight from BRAM
    logic signed [19:0] acc_in;             // Previous accumulation sum
    logic signed [20:0] acc_out;            // Updated sum

    // Counters and resets
    logic       rst_layer1_neuron_cnt;
    logic [7:0] layer1_neuron_count;        // 128 neurons

    logic       rst_layer1_input_cnt;
    logic       mac1_next_input;
    logic [7:0] layer1_input_count;         // 34 inputs
    
    logic       rst_layer2_neuron_cnt;
    logic [7:0] layer2_neuron_count;        // 64 neurons

    logic       rst_layer2_input_cnt;
    logic       mac2_next_input;
    logic [7:0] layer2_input_count;         // 128 inputs
    
    logic       rst_output_layer_neuron_cnt;
    logic [7:0] output_layer_neuron_count;      // 3 neurons

    logic       rst_output_layer_input_cnt;
    logic       mac_output_layer_next_input;
    logic [7:0] output_layer_input_count;       // 64 inputs

    // Layer outputs
    logic [20:0] layer1_outputs     [127:0];
    logic [20:0] layer2_outputs     [63:0];
    logic [20:0] pose_class_outputs [2:0];

    // Intermediate signals to store into larger outputs
    logic [7:0]  current_layer1_weights [33:0];
    logic [7:0]  current_layer1_bias;
    logic [20:0] current_layer1_mac_out;

    logic [7:0]  current_layer2_weights [127:0];
    logic [7:0]  current_layer2_bias;
    logic [20:0] current_layer2_mac_out;

    logic [7:0]  current_output_layer_weights [63:0];
    logic [7:0]  current_output_layer_bias;
    logic [20:0] current_output_layer_mac_out;


    //////////////////////////
    // MODULE INSTANTIATION //
    //////////////////////////

    // BRAM access
    weight_bram_ctrl weight_access(.clk(clk), .rst_n(rst_n),
                                   .new_addr_valid(new_addr_valid), .layer_sel(layer_sel), .neuron(neuron), .input_num(input_num), .bias_sel(bias_sel),
                                   .weight_data_valid(weight_data_valid), .weight_data(weight_data));

    // MAC calculations
    mac mac_unit(.clk(clk), .valid_mac_inputs(valid_mac_inputs), .point(point), .weight(weight), .acc_in(acc_in),
                 .acc_out(acc_out), .valid_mac_out(valid_mac_out));



    //////////////////////////
    //         LOGIC        //
    //////////////////////////

    // State machine flip flop
    always_ff @(posedge clk) begin
        state <= ~rst_n ? IDLE : next_state;
    end

    // Layer 1 Neuron and Input Counter
    always_ff @(posedge clk) begin
        layer1_neuron_count <= (~rst_n | rst_layer1_neuron_cnt) ? 8'd0
                                                                : (next_state == LAYER1_NEURON) ? layer1_neuron_count + 1'b1
                                                                                                : layer1_neuron_count;
    end
    always_ff @(posedge clk) begin
        layer1_input_count <= (~rst_n | rst_layer1_input_cnt) ? 8'd0
                                                              : ((weight_data_valid & (state == LAYER1_INPUTS)) | mac1_next_input) ? layer1_input_count + 1'b1
                                                                                                                                   : layer1_input_count;
    end

    // Flop the mac out to be the next input into the mac
    always_ff @(posedge clk) begin
        current_layer1_mac_out <= ~rst_n ? 21'd0 : ((state == LAYER1_WAIT_MAC) & valid_mac_out) ? acc_out
                                                                                                : current_layer1_mac_out;
    end

    // Flop the mac out to the final output signal
    always_ff @(posedge clk) begin
        layer1_outputs[layer1_neuron_count] <= ~rst_n ? 21'd0
                                                      : (layer1_input_count == 7'd33) & valid_mac_out & (state == LAYER1_WAIT_MAC) ? (acc_out > 0) ? acc_out
                                                                                                                                                   : 21'd0
                                                                                                                                   : layer1_outputs[layer1_neuron_count];
    end



    // Layer 2 Neuron and Input Counter
    always_ff @(posedge clk) begin
        layer2_neuron_count <= (~rst_n | rst_layer2_neuron_cnt) ? 8'd0
                                                                : (next_state == LAYER2_NEURON) ? layer2_neuron_count + 1'b1
                                                                                                : layer2_neuron_count;
    end
    always_ff @(posedge clk) begin
        layer2_input_count <= (~rst_n | rst_layer2_input_cnt) ? 8'd0
                                                              : ((weight_data_valid & (state == LAYER2_INPUTS)) | mac2_next_input) ? layer2_input_count + 1'b1
                                                                                                                                   : layer2_input_count;
    end

    // Flop the mac out to be the next input into the mac
    always_ff @(posedge clk) begin
        current_layer2_mac_out <= ~rst_n ? 21'd0 : ((state == LAYER2_WAIT_MAC) & valid_mac_out) ? acc_out
                                                                                                : current_layer2_mac_out;
    end

    // Flop the mac out to the final output signal
    always_ff @(posedge clk) begin
        layer2_outputs[layer2_neuron_count] <= ~rst_n ? 21'd0
                                                      : (layer2_input_count == 7'd127) & valid_mac_out & (state == LAYER2_WAIT_MAC) ? (acc_out > 0) ? acc_out
                                                                                                                                                    : 21'd0
                                                                                                                                    : layer2_outputs[layer2_neuron_count];
    end


    
    // Output layer Neuron and Input Counter
    always_ff @(posedge clk) begin
        output_layer_neuron_count <= (~rst_n | rst_output_layer_neuron_cnt) ? 8'd0
                                                                            : (next_state == OUTPUT_NEURON) ? output_layer_neuron_count + 1'b1
                                                                                                            : output_layer_neuron_count;
    end
    always_ff @(posedge clk) begin
        output_layer_input_count <= (~rst_n | rst_output_layer_input_cnt) ? 8'd0
                                                                          : ((weight_data_valid & (state == OUTPUT_INPUTS)) | mac_output_layer_next_input) ? output_layer_input_count + 1'b1
                                                                                                                                                           : output_layer_input_count;
    end

    // Flop the mac out to be the next input into the mac
    always_ff @(posedge clk) begin
        current_output_layer_mac_out <= ~rst_n ? 21'd0 : ((state == OUTPUT_WAIT_MAC) & valid_mac_out) ? acc_out
                                                                                                      : current_output_layer_mac_out;
    end

    // Flop the mac out to the final output signal
    always_ff @(posedge clk) begin
        pose_class_outputs[output_layer_neuron_count] <= ~rst_n ? 21'd0
                                                                : (output_layer_input_count == 7'd63) & valid_mac_out & (state == OUTPUT_WAIT_MAC) ? (acc_out > 0) ? acc_out
                                                                                                                                                                   : 21'd0
                                                                                                                                                   : pose_class_outputs[output_layer_neuron_count];
    end

    //FIXME: is movenet_data stable the whole time or should we capture it when movenet_data_valid?
    always_comb begin
        next_state = state;
        done_pulse = 1'b0;

        mac1_next_input = 1'b0;
        rst_layer1_input_cnt = 1'b0;
        rst_layer1_neuron_cnt = 1'b0;

        mac2_next_input = 1'b0;
        rst_layer2_input_cnt = 1'b0;
        rst_layer2_neuron_cnt = 1'b0;

        mac_output_layer_next_input = 1'b0;
        rst_output_layer_input_cnt = 1'b0;
        rst_output_layer_neuron_cnt = 1'b0;

        new_addr_valid = 1'b0;
        valid_mac_inputs = 1'b0;

        case(state)
            IDLE: begin
                next_state = movenet_data_valid ? LAYER1_BIAS : IDLE;

                // Start layer1_inputs with neuron 0 and input 0 access
                new_addr_valid = 1'b1;
                layer_sel = 2'b11;
                bias_sel  = 8'd0;
            end

            // LAYER 1 STATES
            LAYER1_BIAS: begin
                new_addr_valid      = ~weight_data_valid;
                layer_sel           = weight_data_valid ? 2'b00 : 2'b11;
                bias_sel            = layer1_neuron_count;
                current_layer1_bias = weight_data;

                next_state = weight_data_valid ? LAYER1_INPUTS : LAYER1_BIAS;
            end

            LAYER1_INPUTS: begin
                new_addr_valid   = ~weight_data_valid;

                layer_sel = 2'b00;
                neuron    = layer1_neuron_count;
                input_num = layer1_input_count;

                current_layer1_weights[layer1_input_count] = weight_data;

                next_state = (layer1_input_count == 7'd33) & weight_data_valid ? LAYER1_MAC : LAYER1_INPUTS;
                rst_layer1_input_cnt = (layer1_input_count == 7'd33) & weight_data_valid;
            end

            LAYER1_MAC: begin
                valid_mac_inputs = 1'b1;
                acc_in           = (layer1_input_count == 7'd0) ? current_layer1_bias : current_layer1_mac_out;
                point            = movenet_data[layer1_input_count];
                weight           = current_layer1_weights[layer1_input_count];

                next_state = LAYER1_WAIT_MAC;
            end

            LAYER1_WAIT_MAC: begin
                valid_mac_inputs = 1'b0;

                //layer1_outputs[layer1_neuron_count] = (layer1_input_count == 7'd33) & valid_mac_out ? acc_out : 8'd0;
                //current_layer1_mac_out = valid_mac_out ? acc_out : 21'd0;

                mac1_next_input = ~(layer1_input_count == 7'd33) & valid_mac_out;
                rst_layer1_input_cnt = (layer1_input_count == 7'd33) & valid_mac_out;
                next_state = (layer1_input_count == 7'd33) & valid_mac_out ? LAYER1_NEURON
                                                                           : (layer1_input_count != 7'd33) & valid_mac_out ? LAYER1_MAC
                                                                                                                           : LAYER1_WAIT_MAC;
            end
            
            LAYER1_NEURON: begin
                next_state = (layer1_neuron_count == 8'd128) ? LAYER2_BIAS : LAYER1_BIAS;
            end

            //// LAYER 2 STATES
            LAYER2_BIAS: begin
                new_addr_valid      = ~weight_data_valid;
                layer_sel           = weight_data_valid ? 2'b01 : 2'b11;
                bias_sel            = layer2_neuron_count + 8'd128;
                current_layer2_bias = weight_data;

                next_state = weight_data_valid ? LAYER2_INPUTS : LAYER2_BIAS;
            end

            LAYER2_INPUTS: begin
                new_addr_valid   = ~weight_data_valid;

                layer_sel = 2'b01;
                neuron    = layer2_neuron_count;
                input_num = layer2_input_count;

                current_layer2_weights[layer2_input_count] = weight_data;

                next_state = (layer2_input_count == 7'd127) & weight_data_valid ? LAYER2_MAC : LAYER2_INPUTS;
                rst_layer2_input_cnt = (layer2_input_count == 7'd127) & weight_data_valid;
            end
            
            LAYER2_MAC: begin
                valid_mac_inputs = 1'b1;
                acc_in           = (layer2_input_count == 7'd0) ? current_layer2_bias : current_layer2_mac_out;
                point            = layer1_outputs[layer2_input_count];
                weight           = current_layer2_weights[layer2_input_count];

                next_state = LAYER2_WAIT_MAC;
            end

            LAYER2_WAIT_MAC: begin
                valid_mac_inputs = 1'b0;

                mac2_next_input = ~(layer2_input_count == 7'd127) & valid_mac_out;
                rst_layer2_input_cnt = (layer2_input_count == 7'd127) & valid_mac_out;
                next_state = (layer2_input_count == 7'd127) & valid_mac_out ? LAYER2_NEURON
                                                                            : (layer2_input_count != 7'd127) & valid_mac_out ? LAYER2_MAC
                                                                                                                             : LAYER2_WAIT_MAC;
            end
            
            LAYER2_NEURON: begin
                next_state = (layer2_neuron_count == 8'd64) ? OUTPUT_BIAS : LAYER2_BIAS;
            end

            //// OUTPUT LAYER STATES
            OUTPUT_BIAS: begin
                new_addr_valid            = ~weight_data_valid;
                layer_sel                 = weight_data_valid ? 2'b10 : 2'b11;
                bias_sel                  = output_layer_neuron_count + 8'd192;
                current_output_layer_bias = weight_data;

                next_state = weight_data_valid ? OUTPUT_INPUTS : OUTPUT_BIAS;
            end

            OUTPUT_INPUTS: begin
                new_addr_valid   = ~weight_data_valid;

                layer_sel = 2'b10;
                neuron    = output_layer_neuron_count;
                input_num = output_layer_input_count;

                current_output_layer_weights[output_layer_input_count] = weight_data;

                next_state = (output_layer_input_count == 7'd63) & weight_data_valid ? OUTPUT_MAC : OUTPUT_INPUTS;
                rst_output_layer_input_cnt = (output_layer_input_count == 7'd63) & weight_data_valid;
            end
            
            OUTPUT_MAC: begin
                valid_mac_inputs = 1'b1;
                acc_in           = (output_layer_input_count == 7'd0) ? current_output_layer_bias : current_output_layer_mac_out;
                point            = layer2_outputs[output_layer_input_count];
                weight           = current_output_layer_weights[output_layer_input_count];

                next_state = OUTPUT_WAIT_MAC;
            end

            OUTPUT_WAIT_MAC: begin
                valid_mac_inputs = 1'b0;

                mac_output_layer_next_input = ~(output_layer_input_count == 7'd63) & valid_mac_out;
                rst_output_layer_input_cnt = (output_layer_input_count == 7'd63) & valid_mac_out;
                next_state = (output_layer_input_count == 7'd63) & valid_mac_out ? OUTPUT_NEURON
                                                                                 : (output_layer_input_count != 7'd63) & valid_mac_out ? OUTPUT_MAC
                                                                                                                                       : OUTPUT_WAIT_MAC;
            end
            
            OUTPUT_NEURON: begin
                next_state = (output_layer_neuron_count == 8'd3) ? DONE : OUTPUT_BIAS;
            end

            DONE: begin
                done_pulse = 1'b1;
                pose_class = (pose_class_outputs[0] > pose_class_outputs[1]) & (pose_class_outputs[0] > pose_class_outputs[2]) ? 2'b00
                                                                                                                               : (pose_class_outputs[1] > pose_class_outputs[0]) & (pose_class_outputs[1] > pose_class_outputs[2]) ? 2'b01
                                                                                                                                                                                                                                   : (pose_class_outputs[2] > pose_class_outputs[0]) & (pose_class_outputs[2] > pose_class_outputs[1]) ? 2'b10
                                                                                                                                                                                                                                                                                                                                       : 2'b11;

                next_state = IDLE;
            end
        endcase
    end

endmodule
