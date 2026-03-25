`timescale 1ns/1ps

module workout_statemachine_tb;

    localparam int CLK_FREQ    = 10;
    localparam int TIMEOUT_SEC = 5;
    localparam int TIMEOUT_CYC = CLK_FREQ * TIMEOUT_SEC;  // 50 cycles

    // Pose class constants (mirrors DUT)
    localparam logic [2:0] C_PUSHUP_TOP = 3'd0,
                           C_PUSHUP_BOT = 3'd1,
                           C_SQUAT_TOP  = 3'd2,
                           C_SQUAT_BOT  = 3'd3,
                           C_CURL_TOP   = 3'd4,
                           C_CURL_BOT   = 3'd5;

    logic       clk, rst_n;
    logic [2:0] pose_class;
    logic       valid_pulse;
    logic       incr;
    logic [1:0] workout_type;

    workout_statemachine #(
        .CLK_FREQ    (CLK_FREQ),
        .TIMEOUT_SEC (TIMEOUT_SEC)
    ) dut (
        .clk         (clk),
        .rst_n       (rst_n),
        .pose_class  (pose_class),
        .valid_pulse (valid_pulse),
        .incr        (incr),
        .workout_type(workout_type)
    );

    initial clk = 1'b0;
    always  #5 clk = ~clk;
   
    int pass_cnt, fail_cnt;

    task automatic reset_dut();
        rst_n       = 1'b0;
        valid_pulse = 1'b0;
        pose_class  = 3'd0;
        repeat(2) @(posedge clk);
        #1;
        rst_n = 1'b1;
        @(posedge clk);
        #1;
    endtask

    // Drive a one-cycle valid pulse then idle for one more cycle so the
    // registered state update is visible before the next action.
    task automatic send_pose(input logic [2:0] pc);
        pose_class  = pc;
        valid_pulse = 1'b1;
        @(posedge clk); #1;   
        valid_pulse = 1'b0;
        @(posedge clk); #1;   
    endtask

    task automatic wait_cycles(input int n);
        repeat(n) @(posedge clk);
        #1;
    endtask

    task automatic check_1bit(input string name,
                               input logic expected,
                               input logic actual);
        if (expected === actual) begin
            $display("    PASS : %s", name);
            pass_cnt++;
        end else begin
            $display("    FAIL : %s  (expected %0b, got %0b)", name, expected, actual);
            fail_cnt++;
        end
    endtask

    task automatic check_2bit(input string name,
                               input logic [1:0] expected,
                               input logic [1:0] actual);
        if (expected === actual) begin
            $display("    PASS : %s", name);
            pass_cnt++;
        end else begin
            $display("    FAIL : %s  (expected %0d, got %0d)", name, expected, actual);
            fail_cnt++;
        end
    endtask

    // Execute one rep starting FROM the TOP state.
    // Drives bottom then top; captures incr on the top transition.
    task automatic do_rep(input logic [2:0] top_class,
                          input logic [2:0] bot_class,
                          input string      ex_name,
                          input int         rep_num);
        logic captured_incr;

        send_pose(bot_class);

        pose_class  = top_class;
        valid_pulse = 1'b1;
        #1;                      
        captured_incr = incr;
        @(posedge clk); #1;       
        valid_pulse = 1'b0;
        @(posedge clk); #1;

        check_1bit($sformatf("%s rep %0d: incr fires on bottom->top", ex_name, rep_num),
                   1'b1, captured_incr);
    endtask

    // Test: 3-rep sequence for one exercise type
    task automatic test_sequence(input logic [2:0] top_class,
                                 input logic [2:0] bot_class,
                                 input logic [1:0] expected_type,
                                 input string      ex_name);
        $display("  [Sequence] %s", ex_name);
        reset_dut();

        check_2bit($sformatf("%s: starts in IDLE (workout_type==0)", ex_name),
                   2'd0, workout_type);

        send_pose(top_class);
        check_2bit($sformatf("%s: workout_type correct after first TOP", ex_name),
                   expected_type, workout_type);

        for (int i = 1; i <= 3; i++)
            do_rep(top_class, bot_class, ex_name, i);

        check_2bit($sformatf("%s: still in exercise after 3 reps", ex_name),
                   expected_type, workout_type);
    endtask

    // Test: timeout from the TOP state
    task automatic test_timeout_top(input logic [2:0] top_class,
                                    input logic [1:0] expected_type,
                                    input string      ex_name);
        $display("  [Timeout-TOP] %s", ex_name);
        reset_dut();

        send_pose(top_class);
        check_2bit($sformatf("%s TOP: entered exercise", ex_name),
                   expected_type, workout_type);

        wait_cycles(TIMEOUT_CYC + 2);

        check_2bit($sformatf("%s TOP: timed out to IDLE", ex_name),
                   2'd0, workout_type);
    endtask

    // Test: timeout from the BOTTOM state
    task automatic test_timeout_bottom(input logic [2:0] top_class,
                                       input logic [2:0] bot_class,
                                       input logic [1:0] expected_type,
                                       input string      ex_name);
        $display("  [Timeout-BOTTOM] %s", ex_name);
        reset_dut();

        send_pose(top_class);
        send_pose(bot_class);
        check_2bit($sformatf("%s BOTTOM: in exercise after bottom", ex_name),
                   expected_type, workout_type);

        wait_cycles(TIMEOUT_CYC + 2);

        check_2bit($sformatf("%s BOTTOM: timed out to IDLE", ex_name),
                   2'd0, workout_type);
    endtask

    // Test: wrong pose class is ignored
    task automatic test_wrong_class();
        $display("  [Wrong class] wrong poses ignored");
        reset_dut();

        send_pose(C_PUSHUP_TOP);
        check_2bit("wrong class: workout_type stays pushup after squat-bot noise",
                   2'd1, workout_type);

        send_pose(C_SQUAT_BOT);
        check_2bit("wrong class: still in pushup after wrong bottom", 2'd1, workout_type);

        send_pose(C_PUSHUP_BOT);
        pose_class  = C_PUSHUP_TOP;
        valid_pulse = 1'b1;
        #1;
        check_1bit("wrong class: incr fires on valid rep after noise", 1'b1, incr);
        @(posedge clk); #1;
        valid_pulse = 1'b0;
        @(posedge clk); #1;
    endtask

    initial begin
        pass_cnt = 0;
        fail_cnt = 0;

        $display("");
        $display("--- Rep sequence tests ---");
        test_sequence(C_PUSHUP_TOP, C_PUSHUP_BOT, 2'd1, "Pushup");
        test_sequence(C_SQUAT_TOP,  C_SQUAT_BOT,  2'd2, "Squat" );
        test_sequence(C_CURL_TOP,   C_CURL_BOT,   2'd3, "Curl"  );

        $display("");
        $display("--- Timeout from TOP state ---");
        test_timeout_top(C_PUSHUP_TOP, 2'd1, "Pushup");
        test_timeout_top(C_SQUAT_TOP,  2'd2, "Squat" );
        test_timeout_top(C_CURL_TOP,   2'd3, "Curl"  );

        $display("");
        $display("--- Timeout from BOTTOM state ---");
        test_timeout_bottom(C_PUSHUP_TOP, C_PUSHUP_BOT, 2'd1, "Pushup");
        test_timeout_bottom(C_SQUAT_TOP,  C_SQUAT_BOT,  2'd2, "Squat" );
        test_timeout_bottom(C_CURL_TOP,   C_CURL_BOT,   2'd3, "Curl"  );

        $display("");
        $display("--- Robustness tests ---");
        test_wrong_class();

        $display("");
        $display(" Results: %0d passed, %0d failed", pass_cnt, fail_cnt);
        if (fail_cnt == 0)
            $display(" ALL TESTS PASSED");
        else
            $display(" SOME TESTS FAILED");

        $finish;
    end

endmodule
