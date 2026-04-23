`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 04/17/2026 03:10:42 PM
// Design Name: 
// Module Name: mlp_controller_tb
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


module mlp_controller_tb();
    parameter NUM_KP      = 17;    // MoveNet keypoints
    parameter INPUT_WIDTH = 8;     // bits per keypoint value (x or y)
    parameter NUM_INPUTS  = 34;    // 17 keypoints * 2 (x + y)

    // Initialize frames
    localparam NUM_FRAMES = 14;
    logic [INPUT_WIDTH-1:0] frames [NUM_FRAMES-1:0][NUM_INPUTS-1:0];

    logic S_AXI_ACLK;
    logic S_AXI_ARESETN;

    logic [7:0]  S_AXI_AWADDR;
    logic [2:0]  S_AXI_AWPROT;
    logic        S_AXI_AWVALID;
    logic        S_AXI_AWREADY;
    logic [31:0] S_AXI_WDATA;
    logic [3:0]  S_AXI_WSTRB;
    logic        S_AXI_WVALID;
    logic        S_AXI_WREADY;
    logic [1:0]  S_AXI_BRESP;
    logic        S_AXI_BVALID;
    logic        S_AXI_BREADY;
    logic [7:0]  S_AXI_ARADDR;
    logic [2:0]  S_AXI_ARPROT;
    logic        S_AXI_ARVALID;
    logic        S_AXI_ARREADY;
    logic [31:0] S_AXI_RDATA;
    logic [1:0]  S_AXI_RRESP;
    logic        S_AXI_RVALID;
    logic        S_AXI_RREADY;

     mlp_controller_slave_lite_v1_0_S00_AXI mlp_controller(
        .S_AXI_ACLK(S_AXI_ACLK), 
        .S_AXI_ARESETN(S_AXI_ARESETN),

        .S_AXI_AWADDR(S_AXI_AWADDR),
        .S_AXI_AWPROT(S_AXI_AWPROT),
        .S_AXI_AWVALID(S_AXI_AWVALID),
        .S_AXI_AWREADY(S_AXI_AWREADY),
        .S_AXI_WDATA(S_AXI_WDATA),
        .S_AXI_WSTRB(S_AXI_WSTRB),
        .S_AXI_WVALID(S_AXI_WVALID),
        .S_AXI_WREADY(S_AXI_WREADY),
        .S_AXI_BRESP(S_AXI_BRESP),
        .S_AXI_BVALID(S_AXI_BVALID),
        .S_AXI_BREADY(S_AXI_BREADY),
        .S_AXI_ARADDR(S_AXI_ARADDR),
        .S_AXI_ARPROT(S_AXI_ARPROT),
        .S_AXI_ARVALID(S_AXI_ARVALID),
        .S_AXI_ARREADY(S_AXI_ARREADY),
        .S_AXI_RDATA(S_AXI_RDATA),
        .S_AXI_RRESP(S_AXI_RRESP),
        .S_AXI_RVALID(S_AXI_RVALID),
        .S_AXI_RREADY(S_AXI_RREADY)
	);

    // SQUAT FRAMES
    initial begin
        frames[0] = '{
            8'd44,  8'd120,
            8'd40,  8'd123,
            8'd42,  8'd121,
            8'd39,  8'd138,
            8'd44,  8'd130,
            8'd53,  8'd151,
            8'd61,  8'd137,
            8'd78,  8'd144,
            8'd89,  8'd124,
            8'd110, 8'd130,
            8'd88,  8'd112,
            8'd108, 8'd150,
            8'd112, 8'd131,
            8'd162, 8'd154,
            8'd162, 8'd138,
            8'd220, 8'd153,
            8'd212, 8'd142
        };

        frames[1] = '{
            8'd47,  8'd118,
            8'd41,  8'd120,
            8'd43,  8'd119,
            8'd41,  8'd137,
            8'd45,  8'd132,
            8'd55,  8'd150,
            8'd63,  8'd137,
            8'd90,  8'd139,
            8'd76,  8'd132,
            8'd122, 8'd121,
            8'd86,  8'd122,
            8'd118, 8'd144,
            8'd117, 8'd133,
            8'd165, 8'd150,
            8'd161, 8'd133,
            8'd220, 8'd153,
            8'd212, 8'd143
        };

        frames[2] = '{
            8'd47, 8'd114,
            8'd41, 8'd119,
            8'd43, 8'd120,
            8'd40, 8'd129,
            8'd40, 8'd135,
            8'd52, 8'd144,
            8'd55, 8'd146,
            8'd84, 8'd123,
            8'd87, 8'd127,
            8'd100, 8'd104,
            8'd111, 8'd100,
            8'd111, 8'd153,
            8'd112, 8'd152,
            8'd160, 8'd137,
            8'd158, 8'd129,
            8'd217, 8'd152,
            8'd213, 8'd143
        };

        frames[3] = '{
            8'd67,  8'd101,
            8'd61,  8'd103,
            8'd66,  8'd102,
            8'd63,  8'd120,
            8'd69,  8'd118,
            8'd83,  8'd120,
            8'd87,  8'd120,
            8'd99,  8'd65,
            8'd99,  8'd74,
            8'd105, 8'd16,
            8'd109, 8'd33,
            8'd138, 8'd169,
            8'd136, 8'd161,
            8'd172, 8'd99,
            8'd168, 8'd99,
            8'd222, 8'd147,
            8'd216, 8'd143
        };

        frames[4] = '{
            8'd102, 8'd87,
            8'd99,  8'd88,
            8'd101, 8'd88,
            8'd99,  8'd99,
            8'd101, 8'd99,
            8'd111, 8'd111,
            8'd115, 8'd108,
            8'd114, 8'd66,
            8'd115, 8'd76,
            8'd117, 8'd24,
            8'd123, 8'd21,
            8'd161, 8'd171,
            8'd162, 8'd162,
            8'd176, 8'd100,
            8'd173, 8'd97,
            8'd224, 8'd150,
            8'd216, 8'd143
        };

        frames[5] = '{
            8'd76,  8'd101,
            8'd65,  8'd102,
            8'd72,  8'd101,
            8'd62,  8'd113,
            8'd78,  8'd117,
            8'd84,  8'd111,
            8'd87,  8'd132,
            8'd99,  8'd74,
            8'd104, 8'd90,
            8'd105, 8'd25,
            8'd114, 8'd61,
            8'd144, 8'd174,
            8'd137, 8'd181,
            8'd172, 8'd100,
            8'd168, 8'd106,
            8'd224, 8'd148,
            8'd214, 8'd144
        };

        frames[6] = '{
            8'd47,  8'd117,
            8'd40,  8'd120,
            8'd44,  8'd119,
            8'd39,  8'd135,
            8'd45,  8'd131,
            8'd52,  8'd131,
            8'd57,  8'd144,
            8'd92,  8'd114,
            8'd90,  8'd121,
            8'd115, 8'd86,
            8'd110, 8'd91,
            8'd111, 8'd152,
            8'd112, 8'd149,
            8'd162, 8'd143,
            8'd159, 8'd133,
            8'd223, 8'd153,
            8'd213, 8'd143
        };

        frames[7] = '{
            8'd44,  8'd121,
            8'd40,  8'd121,
            8'd44,  8'd120,
            8'd40,  8'd136,
            8'd48,  8'd131,
            8'd54,  8'd147,
            8'd61,  8'd145,
            8'd76,  8'd130,
            8'd77,  8'd125,
            8'd53,  8'd129,
            8'd51,  8'd125,
            8'd112, 8'd145,
            8'd112, 8'd135,
            8'd168, 8'd155,
            8'd165, 8'd142,
            8'd219, 8'd154,
            8'd212, 8'd142
        };

        frames[8] = '{
            8'd48,  8'd120,
            8'd43,  8'd123,
            8'd45,  8'd121,
            8'd40,  8'd133,
            8'd50,  8'd133,
            8'd51,  8'd147,
            8'd59,  8'd141,
            8'd74,  8'd137,
            8'd87,  8'd124,
            8'd54,  8'd125,
            8'd49,  8'd125,
            8'd111, 8'd145,
            8'd114, 8'd131,
            8'd165, 8'd151,
            8'd162, 8'd136,
            8'd217, 8'd156,
            8'd211, 8'd144
        };

        frames[9] = '{
            8'd64,  8'd102,
            8'd58,  8'd106,
            8'd62,  8'd106,
            8'd56,  8'd119,
            8'd63,  8'd115,
            8'd73,  8'd128,
            8'd76,  8'd136,
            8'd114, 8'd108,
            8'd89,  8'd144,
            8'd99,  8'd99,
            8'd84,  8'd122,
            8'd138, 8'd159,
            8'd137, 8'd160,
            8'd170, 8'd95,
            8'd168, 8'd95,
            8'd222, 8'd148,
            8'd214, 8'd141
        };

        frames[10] = '{
            8'd99,  8'd79,
            8'd96,  8'd81,
            8'd98,  8'd81,
            8'd100, 8'd94,
            8'd102, 8'd94,
            8'd117, 8'd103,
            8'd114, 8'd104,
            8'd149, 8'd78,
            8'd144, 8'd79,
            8'd152, 8'd41,
            8'd145, 8'd61,
            8'd165, 8'd148,
            8'd164, 8'd143,
            8'd177, 8'd97,
            8'd174, 8'd97,
            8'd219, 8'd150,
            8'd216, 8'd137
        };

        frames[11] = '{
            8'd92,  8'd90,
            8'd87,  8'd90,
            8'd88,  8'd90,
            8'd89,  8'd104,
            8'd91,  8'd103,
            8'd113, 8'd115,
            8'd104, 8'd108,
            8'd142, 8'd101,
            8'd96,  8'd86,
            8'd139, 8'd59,
            8'd88,  8'd87,
            8'd164, 8'd139,
            8'd158, 8'd128,
            8'd176, 8'd98,
            8'd176, 8'd96,
            8'd220, 8'd151,
            8'd213, 8'd138
        };

        frames[12] = '{
            8'd50,  8'd120,
            8'd47,  8'd123,
            8'd52,  8'd117,
            8'd51,  8'd135,
            8'd58,  8'd119,
            8'd66,  8'd145,
            8'd77,  8'd120,
            8'd98,  8'd124,
            8'd96,  8'd123,
            8'd98,  8'd99,
            8'd103, 8'd94,
            8'd126, 8'd169,
            8'd127, 8'd151,
            8'd168, 8'd113,
            8'd165, 8'd111,
            8'd223, 8'd152,
            8'd217, 8'd141
        };

        frames[13] = '{
            8'd41,  8'd132,
            8'd38,  8'd136,
            8'd38,  8'd128,
            8'd42,  8'd144,
            8'd44,  8'd128,
            8'd54,  8'd156,
            8'd66,  8'd130,
            8'd87,  8'd143,
            8'd92,  8'd122,
            8'd74,  8'd107,
            8'd103, 8'd96,
            8'd111, 8'd156,
            8'd119, 8'd136,
            8'd162, 8'd141,
            8'd160, 8'd131,
            8'd221, 8'd153,
            8'd208, 8'd142
        };

    end

    // =========================
    // AXI WRITE TASK
    // =========================
    task automatic axi_write(input [7:0] addr, input [31:0] data);
    begin
        @(posedge S_AXI_ACLK);

        S_AXI_AWADDR  <= addr;
        S_AXI_AWVALID <= 1;
        S_AXI_WDATA   <= data;
        S_AXI_WVALID  <= 1;
        S_AXI_WSTRB   <= 4'b1111;
        S_AXI_BREADY  <= 1;

        wait (S_AXI_AWREADY && S_AXI_WREADY);

        @(posedge S_AXI_ACLK);
        S_AXI_AWVALID <= 0;
        S_AXI_WVALID  <= 0;

        wait (S_AXI_BVALID);

        @(posedge S_AXI_ACLK);
        S_AXI_BREADY <= 0;
    end
    endtask

    // =========================
    // AXI READ TASK
    // =========================
    task automatic axi_read(input [7:0] addr, output [31:0] data);
    begin
        @(posedge S_AXI_ACLK);

        S_AXI_ARADDR  <= addr;
        S_AXI_ARVALID <= 1;
        S_AXI_RREADY  <= 1;

        wait (S_AXI_ARREADY);

        @(posedge S_AXI_ACLK);
        S_AXI_ARVALID <= 0;

        wait (S_AXI_RVALID);
        data = S_AXI_RDATA;

        @(posedge S_AXI_ACLK);
        S_AXI_RREADY <= 0;
    end
    endtask

    task automatic load_frame(input int frame_index);
        $display("\n[TB] Loading frame %0d at time %0t", frame_index, $time);
 
        for (int i = 1; i < NUM_INPUTS; i++) begin
            axi_write(i*4, {24'd0, frames[frame_index][i]});
        end

        // trigger start (adjust address if needed)
        axi_write(8'h90, 0);
        @(posedge S_AXI_ACLK);
        axi_write(8'h8c, 1);
        @(posedge S_AXI_ACLK);
        axi_write(8'h8c, 0);
    endtask

    reg [31:0] status;
    task automatic wait_for_done();
        //reg [31:0] status;
        begin
            while (1) begin
                axi_read(8'h90, status); // done register
                if (status == 1) break;
                @(posedge S_AXI_ACLK);
            end
        end
    endtask

    task automatic print_outputs();
        reg [31:0] result;
        begin
            axi_read(8'h94, result);

            $display("[TB] MLP output:");
            case(result[1:0])
                2'b00: $display(" PUSH UP");
                2'b01: $display(" SQUAT");
                2'b10: $display(" CURL");
                default: $display(" IDLE");
            endcase
        end
    endtask

    initial begin
        // init AXI signals
        S_AXI_ACLK    = 0;
        S_AXI_ARESETN = 0;

        S_AXI_AWVALID = 0;
        S_AXI_WVALID  = 0;
        S_AXI_BREADY  = 0;
        S_AXI_ARVALID = 0;
        S_AXI_RREADY  = 0;

        S_AXI_AWPROT = 0;
        S_AXI_ARPROT = 0;

        // reset
        repeat(5) @(posedge S_AXI_ACLK);
        S_AXI_ARESETN = 1;

        repeat(2) @(posedge S_AXI_ACLK);

        // run frames
        for (int f = 0; f < NUM_FRAMES; f++) begin
            load_frame(f);
            wait_for_done();
            print_outputs();
            repeat(5) @(posedge S_AXI_ACLK);
        end

        $display("\n[TB] All frames complete.");
        $stop();
    end

    always
        #5 S_AXI_ACLK = ~S_AXI_ACLK;

endmodule
