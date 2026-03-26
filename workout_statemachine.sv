// Detects exercise repetitions by tracking TOP -> BOTTOM -> TOP transitions.
// Outputs a one-cycle incr pulse on each completed rep and the active workout type.
// Times out to IDLE after TIMEOUT_SEC seconds with no valid state transition.
//
// pose_class encoding:
//   3'd0 = Pushup top    3'd1 = Pushup bottom
//   3'd2 = Squat top     3'd3 = Squat bottom
//   3'd4 = Curl top      3'd5 = Curl bottom
//
// workout_type encoding: 0 = idle, 1 = pushup, 2 = squat, 3 = curl

module workout_statemachine #(
    parameter int CLK_FREQ    = 50_000_000,  // Hz
    parameter int TIMEOUT_SEC = 5
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [2:0]  pose_class,   // From classifier
    input  wire        valid_pulse,  // One-cycle pulse when pose_class is valid
    output logic       incr,         // One-cycle pulse on completed rep
    output logic [1:0] workout_type  // Active exercise type
);

    // Timeout counter
    localparam int TIMEOUT_CYCLES = CLK_FREQ * TIMEOUT_SEC;
    localparam int TIMER_W        = $clog2(TIMEOUT_CYCLES + 1);

    // Pose class constants
    localparam logic [2:0] C_PUSHUP_TOP = 3'd0,
                           C_PUSHUP_BOT = 3'd1,
                           C_SQUAT_TOP  = 3'd2,
                           C_SQUAT_BOT  = 3'd3,
                           C_CURL_TOP   = 3'd4,
                           C_CURL_BOT   = 3'd5;

    typedef enum logic [2:0] {
        IDLE,
        PUSHUP_TOP, PUSHUP_BOTTOM,
        SQUAT_TOP,  SQUAT_BOTTOM,
        CURL_TOP,   CURL_BOTTOM
    } state_t;

    state_t             cur_state, nxt_state;
    logic [TIMER_W-1:0] timer;
    logic               timeout;

    // Timeout fires when we have been stuck in the same state for TIMEOUT_CYCLES
    assign timeout = (timer >= TIMER_W'(TIMEOUT_CYCLES));

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            timer <= '0;
        else if (nxt_state != cur_state)
            timer <= '0;
        else
            timer <= timer + 1'b1;
    end


    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cur_state <= IDLE;
        else
            cur_state <= nxt_state;
    end

  
    always_comb begin
        nxt_state = cur_state;
        incr      = 1'b0;

        case (cur_state)

            IDLE: begin
                if (valid_pulse)
                    case (pose_class)
                        C_PUSHUP_TOP: nxt_state = PUSHUP_TOP;
                        C_SQUAT_TOP:  nxt_state = SQUAT_TOP;
                        C_CURL_TOP:   nxt_state = CURL_TOP;
                        default:      nxt_state = IDLE;
                    endcase
            end

            PUSHUP_TOP: begin
                if (timeout)
                    nxt_state = IDLE;
                else if (valid_pulse && pose_class == C_PUSHUP_BOT)
                    nxt_state = PUSHUP_BOTTOM;
            end

            PUSHUP_BOTTOM: begin
                if (timeout)
                    nxt_state = IDLE;
                else if (valid_pulse && pose_class == C_PUSHUP_TOP) begin
                    nxt_state = PUSHUP_TOP;
                    incr      = 1'b1;
                end
            end

            SQUAT_TOP: begin
                if (timeout)
                    nxt_state = IDLE;
                else if (valid_pulse && pose_class == C_SQUAT_BOT)
                    nxt_state = SQUAT_BOTTOM;
            end

            SQUAT_BOTTOM: begin
                if (timeout)
                    nxt_state = IDLE;
                else if (valid_pulse && pose_class == C_SQUAT_TOP) begin
                    nxt_state = SQUAT_TOP;
                    incr      = 1'b1;
                end
            end

            CURL_TOP: begin
                if (timeout)
                    nxt_state = IDLE;
                else if (valid_pulse && pose_class == C_CURL_BOT)
                    nxt_state = CURL_BOTTOM;
            end

            CURL_BOTTOM: begin
                if (timeout)
                    nxt_state = IDLE;
                else if (valid_pulse && pose_class == C_CURL_TOP) begin
                    nxt_state = CURL_TOP;
                    incr      = 1'b1;
                end
            end

            default: nxt_state = IDLE;

        endcase
    end

    // Workout type output
    always_comb begin
        case (cur_state)
            PUSHUP_TOP, PUSHUP_BOTTOM: workout_type = 2'd1;
            SQUAT_TOP,  SQUAT_BOTTOM:  workout_type = 2'd2;
            CURL_TOP,   CURL_BOTTOM:   workout_type = 2'd3;
            default:                   workout_type = 2'd0;
        endcase
    end

endmodule
