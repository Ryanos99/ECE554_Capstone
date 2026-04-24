// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2025 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2025.2 (win64) Build 6299465 Fri Nov 14 19:35:11 GMT 2025
// Date        : Mon Apr 20 19:17:55 2026
// Host        : Madis_ThinkPad running 64-bit major release  (build 9200)
// Command     : write_verilog -force -mode funcsim
//               z:/ece554_final_project/ip_repo/mlp_controller_1_0/src/blk_mem_gen_0_1/blk_mem_gen_0_sim_netlist.v
// Design      : blk_mem_gen_0
// Purpose     : This verilog netlist is a functional simulation representation of the design and should not be modified
//               or synthesized. This netlist cannot be used for SDF annotated simulation.
// Device      : xczu3eg-sfvc784-2-e
// --------------------------------------------------------------------------------
`timescale 1 ps / 1 ps

(* CHECK_LICENSE_TYPE = "blk_mem_gen_0,blk_mem_gen_v8_4_12,{}" *) (* downgradeipidentifiedwarnings = "yes" *) (* x_core_info = "blk_mem_gen_v8_4_12,Vivado 2025.2" *) 
(* NotValidForBitStream *)
module blk_mem_gen_0
   (clka,
    ena,
    addra,
    douta);
  (* x_interface_info = "xilinx.com:interface:bram:1.0 BRAM_PORTA CLK" *) (* x_interface_mode = "slave BRAM_PORTA" *) (* x_interface_parameter = "XIL_INTERFACENAME BRAM_PORTA, MEM_ADDRESS_MODE BYTE_ADDRESS, MEM_SIZE 8192, MEM_WIDTH 32, MEM_ECC NONE, MASTER_TYPE OTHER, READ_LATENCY 1" *) input clka;
  (* x_interface_info = "xilinx.com:interface:bram:1.0 BRAM_PORTA EN" *) input ena;
  (* x_interface_info = "xilinx.com:interface:bram:1.0 BRAM_PORTA ADDR" *) input [13:0]addra;
  (* x_interface_info = "xilinx.com:interface:bram:1.0 BRAM_PORTA DOUT" *) output [7:0]douta;

  wire [13:0]addra;
  wire clka;
  wire [7:0]douta;
  wire ena;
  wire NLW_U0_dbiterr_UNCONNECTED;
  wire NLW_U0_rsta_busy_UNCONNECTED;
  wire NLW_U0_rstb_busy_UNCONNECTED;
  wire NLW_U0_s_axi_arready_UNCONNECTED;
  wire NLW_U0_s_axi_awready_UNCONNECTED;
  wire NLW_U0_s_axi_bvalid_UNCONNECTED;
  wire NLW_U0_s_axi_dbiterr_UNCONNECTED;
  wire NLW_U0_s_axi_rlast_UNCONNECTED;
  wire NLW_U0_s_axi_rvalid_UNCONNECTED;
  wire NLW_U0_s_axi_sbiterr_UNCONNECTED;
  wire NLW_U0_s_axi_wready_UNCONNECTED;
  wire NLW_U0_sbiterr_UNCONNECTED;
  wire [7:0]NLW_U0_doutb_UNCONNECTED;
  wire [13:0]NLW_U0_rdaddrecc_UNCONNECTED;
  wire [3:0]NLW_U0_s_axi_bid_UNCONNECTED;
  wire [1:0]NLW_U0_s_axi_bresp_UNCONNECTED;
  wire [13:0]NLW_U0_s_axi_rdaddrecc_UNCONNECTED;
  wire [7:0]NLW_U0_s_axi_rdata_UNCONNECTED;
  wire [3:0]NLW_U0_s_axi_rid_UNCONNECTED;
  wire [1:0]NLW_U0_s_axi_rresp_UNCONNECTED;

  (* C_ADDRA_WIDTH = "14" *) 
  (* C_ADDRB_WIDTH = "14" *) 
  (* C_ALGORITHM = "1" *) 
  (* C_AXI_ID_WIDTH = "4" *) 
  (* C_AXI_SLAVE_TYPE = "0" *) 
  (* C_AXI_TYPE = "1" *) 
  (* C_BYTE_SIZE = "9" *) 
  (* C_COMMON_CLK = "0" *) 
  (* C_COUNT_18K_BRAM = "1" *) 
  (* C_COUNT_36K_BRAM = "3" *) 
  (* C_CTRL_ECC_ALGO = "NONE" *) 
  (* C_DEFAULT_DATA = "0" *) 
  (* C_DISABLE_WARN_BHV_COLL = "0" *) 
  (* C_DISABLE_WARN_BHV_RANGE = "0" *) 
  (* C_ELABORATION_DIR = "./" *) 
  (* C_ENABLE_32BIT_ADDRESS = "0" *) 
  (* C_EN_DEEPSLEEP_PIN = "0" *) 
  (* C_EN_ECC_PIPE = "0" *) 
  (* C_EN_RDADDRA_CHG = "0" *) 
  (* C_EN_RDADDRB_CHG = "0" *) 
  (* C_EN_SAFETY_CKT = "0" *) 
  (* C_EN_SHUTDOWN_PIN = "0" *) 
  (* C_EN_SLEEP_PIN = "0" *) 
  (* C_EST_POWER_SUMMARY = "Estimated Power for IP     :     1.8981 mW" *) 
  (* C_FAMILY = "zynquplus" *) 
  (* C_HAS_AXI_ID = "0" *) 
  (* C_HAS_ENA = "1" *) 
  (* C_HAS_ENB = "0" *) 
  (* C_HAS_INJECTERR = "0" *) 
  (* C_HAS_MEM_OUTPUT_REGS_A = "1" *) 
  (* C_HAS_MEM_OUTPUT_REGS_B = "0" *) 
  (* C_HAS_MUX_OUTPUT_REGS_A = "0" *) 
  (* C_HAS_MUX_OUTPUT_REGS_B = "0" *) 
  (* C_HAS_REGCEA = "0" *) 
  (* C_HAS_REGCEB = "0" *) 
  (* C_HAS_RSTA = "0" *) 
  (* C_HAS_RSTB = "0" *) 
  (* C_HAS_SOFTECC_INPUT_REGS_A = "0" *) 
  (* C_HAS_SOFTECC_OUTPUT_REGS_B = "0" *) 
  (* C_INITA_VAL = "0" *) 
  (* C_INITB_VAL = "0" *) 
  (* C_INIT_FILE = "blk_mem_gen_0.mem" *) 
  (* C_INIT_FILE_NAME = "blk_mem_gen_0.mif" *) 
  (* C_INTERFACE_TYPE = "0" *) 
  (* C_LOAD_INIT_FILE = "1" *) 
  (* C_MEM_TYPE = "3" *) 
  (* C_MUX_PIPELINE_STAGES = "0" *) 
  (* C_PRIM_TYPE = "1" *) 
  (* C_READ_DEPTH_A = "13187" *) 
  (* C_READ_DEPTH_B = "13187" *) 
  (* C_READ_LATENCY_A = "1" *) 
  (* C_READ_LATENCY_B = "1" *) 
  (* C_READ_WIDTH_A = "8" *) 
  (* C_READ_WIDTH_B = "8" *) 
  (* C_RSTRAM_A = "0" *) 
  (* C_RSTRAM_B = "0" *) 
  (* C_RST_PRIORITY_A = "CE" *) 
  (* C_RST_PRIORITY_B = "CE" *) 
  (* C_SIM_COLLISION_CHECK = "ALL" *) 
  (* C_USE_BRAM_BLOCK = "0" *) 
  (* C_USE_BYTE_WEA = "0" *) 
  (* C_USE_BYTE_WEB = "0" *) 
  (* C_USE_DEFAULT_DATA = "0" *) 
  (* C_USE_ECC = "0" *) 
  (* C_USE_SOFTECC = "0" *) 
  (* C_USE_URAM = "0" *) 
  (* C_WEA_WIDTH = "1" *) 
  (* C_WEB_WIDTH = "1" *) 
  (* C_WRITE_DEPTH_A = "13187" *) 
  (* C_WRITE_DEPTH_B = "13187" *) 
  (* C_WRITE_MODE_A = "WRITE_FIRST" *) 
  (* C_WRITE_MODE_B = "WRITE_FIRST" *) 
  (* C_WRITE_WIDTH_A = "8" *) 
  (* C_WRITE_WIDTH_B = "8" *) 
  (* C_XDEVICEFAMILY = "zynquplus" *) 
  (* downgradeipidentifiedwarnings = "yes" *) 
  (* is_du_within_envelope = "true" *) 
  blk_mem_gen_0_blk_mem_gen_v8_4_12 U0
       (.addra(addra),
        .addrb({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .clka(clka),
        .clkb(1'b0),
        .dbiterr(NLW_U0_dbiterr_UNCONNECTED),
        .deepsleep(1'b0),
        .dina({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .dinb({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .douta(douta),
        .doutb(NLW_U0_doutb_UNCONNECTED[7:0]),
        .eccpipece(1'b0),
        .ena(ena),
        .enb(1'b0),
        .injectdbiterr(1'b0),
        .injectsbiterr(1'b0),
        .rdaddrecc(NLW_U0_rdaddrecc_UNCONNECTED[13:0]),
        .regcea(1'b1),
        .regceb(1'b1),
        .rsta(1'b0),
        .rsta_busy(NLW_U0_rsta_busy_UNCONNECTED),
        .rstb(1'b0),
        .rstb_busy(NLW_U0_rstb_busy_UNCONNECTED),
        .s_aclk(1'b0),
        .s_aresetn(1'b0),
        .s_axi_araddr({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .s_axi_arburst({1'b0,1'b0}),
        .s_axi_arid({1'b0,1'b0,1'b0,1'b0}),
        .s_axi_arlen({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .s_axi_arready(NLW_U0_s_axi_arready_UNCONNECTED),
        .s_axi_arsize({1'b0,1'b0,1'b0}),
        .s_axi_arvalid(1'b0),
        .s_axi_awaddr({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .s_axi_awburst({1'b0,1'b0}),
        .s_axi_awid({1'b0,1'b0,1'b0,1'b0}),
        .s_axi_awlen({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .s_axi_awready(NLW_U0_s_axi_awready_UNCONNECTED),
        .s_axi_awsize({1'b0,1'b0,1'b0}),
        .s_axi_awvalid(1'b0),
        .s_axi_bid(NLW_U0_s_axi_bid_UNCONNECTED[3:0]),
        .s_axi_bready(1'b0),
        .s_axi_bresp(NLW_U0_s_axi_bresp_UNCONNECTED[1:0]),
        .s_axi_bvalid(NLW_U0_s_axi_bvalid_UNCONNECTED),
        .s_axi_dbiterr(NLW_U0_s_axi_dbiterr_UNCONNECTED),
        .s_axi_injectdbiterr(1'b0),
        .s_axi_injectsbiterr(1'b0),
        .s_axi_rdaddrecc(NLW_U0_s_axi_rdaddrecc_UNCONNECTED[13:0]),
        .s_axi_rdata(NLW_U0_s_axi_rdata_UNCONNECTED[7:0]),
        .s_axi_rid(NLW_U0_s_axi_rid_UNCONNECTED[3:0]),
        .s_axi_rlast(NLW_U0_s_axi_rlast_UNCONNECTED),
        .s_axi_rready(1'b0),
        .s_axi_rresp(NLW_U0_s_axi_rresp_UNCONNECTED[1:0]),
        .s_axi_rvalid(NLW_U0_s_axi_rvalid_UNCONNECTED),
        .s_axi_sbiterr(NLW_U0_s_axi_sbiterr_UNCONNECTED),
        .s_axi_wdata({1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0}),
        .s_axi_wlast(1'b0),
        .s_axi_wready(NLW_U0_s_axi_wready_UNCONNECTED),
        .s_axi_wstrb(1'b0),
        .s_axi_wvalid(1'b0),
        .sbiterr(NLW_U0_sbiterr_UNCONNECTED),
        .shutdown(1'b0),
        .sleep(1'b0),
        .wea(1'b0),
        .web(1'b0));
endmodule
`pragma protect begin_protected
`pragma protect version = 1
`pragma protect encrypt_agent = "XILINX"
`pragma protect encrypt_agent_info = "Xilinx Encryption Tool 2025.2"
`pragma protect key_keyowner="Synopsys", key_keyname="SNPS-VCS-RSA-2", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=128)
`pragma protect key_block
YqH9kwIC39+qbZg4PSfFsXuB9k9wnuxNryS/CfnEri6Ci9fSC6fsrQ/T/hnt3u/yolbJ8DJa1Qu6
Qnm24A9jLbA+fu3Nsmm6/rM6a4vU6OfVl/gTFd/CiWDutv6Dhn6Lim4uUNPahoOR/A2Yc4Zo2tdI
kMLO9gn9WlH2l3O2oXs=

`pragma protect key_keyowner="Aldec", key_keyname="ALDEC15_001", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=256)
`pragma protect key_block
XJYO2VHd/cnMxQd3i7/2qRhl57dl+doEKuhAunQyv3vpGRG/jlNxj8PqrgLoF0HMdqE3qJUVE/oq
kBSapqjVjLDMOrNGQ+Tc6VGsKMZH8FE/TXHQJ/IM5Iuiu2eozEwwVUomF+7cfqn+9OsVsqCONQ1M
g0oRlangiqasJDhhMfnlGGqwAwmgWRGQA6dmhTuua1s8zdvIv540zY6p5au8cAKVhqyyKK7wbxEE
SGuFqX+NYoyRV+rfWCcWM+hJEmnWS8LNAKkd13YE2+17sPYzUdZ23DmTxXK6KlAxKFW27CBySUfg
qdNXp2DSs2KAQYih27pBNMuHfGbM/ATFPWFvxg==

`pragma protect key_keyowner="Mentor Graphics Corporation", key_keyname="MGC-VELOCE-RSA", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=128)
`pragma protect key_block
lYoEi/e8HsDTz6N11EDe/B/iitERmeYndlCklmCluwgb0N4W80JUGVlkd7NlRZHRNhxaNBJPkcjC
n61nO0tb17NwsMwjbY5TF8JWRYTNw1JXCFacvQYrdKv4/7QNQEtwVGiCLxFhOA8aHlWMZIrc2fri
VRMVWaEBcPwCGorlVIM=

`pragma protect key_keyowner="Mentor Graphics Corporation", key_keyname="MGC-VERIF-SIM-RSA-2", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=256)
`pragma protect key_block
QEw9fEsWFbdX0OQLvYs/gl+zyEOW3ak9TdQVaq+0AXXOT3LIqF7wDxJ6ZBnlf9mNbdsUVH5tAz1o
H8u7ihJl1L3THEvugW+TS8hkvVbEA9rKO2vV15KAj4Lla7UdFT/xDfe79RFarlLI7yGrubjgdoRi
QWy//UKsffG7IWNwmoSuppWiWB4ZHJtkunNyIkm70JPGyZF62VxJg1MTT+5LUbZG5vZjjuHZud9w
xJaKv1tFP/x8RVqLU5gPOqGqTW7/nKO2S+450Vo4D9vAmBVVcXpaL1EbSmCvQ+qJmcQKtf9qYFRV
Zko08hbpHjPxstqvTDro01jRzB8592m4xU2TWA==

`pragma protect key_keyowner="Real Intent", key_keyname="RI-RSA-KEY-1", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=256)
`pragma protect key_block
TC7q853CWBPPJgbRfgDV1lmjUwSAtliljShAyNFg8sfRfwDzchthzoSPH1UCHV++E2JXacEKq1lB
UWsNP92U4Xh0/Gu+6esOI0pJb8I+TRTxyBN1I4cRQEfQHcwfhbSdeH3yX9OV3opLEqYmT37hWU+J
zCawYnxVESI0FtRzEXve9gdEWlrKKckrT/hp4mvxxOjvOkOSQBvy0elgUOqh6mEOZl+JnUbsR+Wm
CoZLE1eefMZy3FnVmyDNPv3JPXi88aLXMyimal0MYFkTiS4XJiGT3eAIMIbksehXY+eYi/KFpZWQ
GHpX+lG3UmiWWLwyPakFwKEHbrBc70AlJ2eV9g==

`pragma protect key_keyowner="Xilinx", key_keyname="xilinxt_2025.1-2029.x", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=256)
`pragma protect key_block
j9nmCKgjPWNChPbpSW6EWLrMA6oCG2JGPoum8px09v0PEAh0DRXZi0J8HPzXUsZgOEMcKpA7X54u
YFcDDCLAQ+urha/eSPbQYHQh4yGCursxAQ1C6LEyNQ2wJ0eLlO2bJeAl/gof06zqsYVM2lLJVNv5
wao1k2bmgPdfpfY3c9vPD0fSMuZPS41EoRS0cQhO5GTZnKdjxm6tEUL3GnTjB8ynSCIbCJUsMtAX
4FRHNa52gudx5B5fagR+lXgFhE7e++rWTJELr7SYB+r5Es8qZLTpCH8TrQxEkV0rY/+e4sAjNE2D
gHw8GD7VcUtc15B8y1BbVmh29qc8Nd3V2i/miA==

`pragma protect key_keyowner="Metrics Technologies Inc.", key_keyname="DSim", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=256)
`pragma protect key_block
UkCD6I/Vye4qNoNoa3hIexBXG3xyKUJPAHAjIo7UcNVCDXpMQiYEtPDqExZMfiPlJn2nswCYIfIJ
FYWqMCloKSQyyI/7yZ2EtbyWEklb/P5IyZyvGi6hhFUo/JFTb12b4bK0gZPr+bCDdlVQKTx5GVHz
wptdUJO2omSj8axVMPbLRRtVzlJIZ29dTJ2ATXVXAcBxPnFfHRAMnYYKLeeLExX61vQvpqrkLQHm
XG7hpVzJi56gYKAzxa2BLq072OCVpVS70bfWlhlSTVcSlCrUf+EcarEk4FD8+Ih2NCvrqremG6yn
TtcBn8Xr8M/6zhOYvLi6AD6eArDMKA8n+Ccv8A==

`pragma protect key_keyowner="Atrenta", key_keyname="ATR-SG-RSA-1", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=384)
`pragma protect key_block
A5y5QVZU8yjPexRVPioSiAGohCHD5DX5FVobuMyhcgQRExLUhPvnnS8HOtxTj/2IapEcz68gFMGG
Hpi+m725u85/om/Vze9pGIW9Mn328Kz2FIg3W5EvGstfGwY+48LiAGAmTR269JS4lJGVYWYOz7Xk
S8cEsFd2m7j8iyKtARJzD90+UdXq/cIIh725jC9i8nbgxB364zddvm1Z/DF3JRw1qFp6GGcuRai1
KNcJ1j8c9wtIgktpsteU3e5+bxHEw8NT3gWXUFYjm00NDq97Jals8Jjktmum2nQxoF7ivPacfEey
gnSF6jRMkTsZObzc30hAhs0CEtc33hZLhPLHSn8pQ0WyvKJLHdd5s2yckgTZtqxC1Sbwe7WEgNXe
ZMX3pIkz+aoXsAL7GBLyVBMVQcyMoF0w8QGAaTe8sqatABwPqXidYRqNROTf62IYcMpV89XYgaTv
EwIn/oni9KOFd2BFVxRZbFGGC4IjvigsTBUijI+Dk6kVnDh240clGcc4

`pragma protect key_keyowner="Cadence Design Systems.", key_keyname="CDS_RSA_KEY_VER_1", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=256)
`pragma protect key_block
Omtp+lCaqUx7Z4qdFj2zrN8LpCkit2eX4hlMtig+ielGm/x4FSZkpjoFmiqdKFPi2eg0pg09MSai
XyGH68UzAR7Xrj8f1jlIoUmMKp4GcxfdqfTeuu7kWGOJEP6cvgTjSJFj2gawDv7f4yZcltnK2x0L
e4GW/rBTmGvZtKWb2ahjINLxPuh3dDaSaWdb+zVgbtyrI5FrjxBkq+aOxSjyNsqnCx1L0uWbxnkl
88NbXN3dTaECXHNm/fsleayM5hKis7kTv9BFajJMGy+BhQlmIYpE+F5zchnTTFUFJZCz1sX9Fc8e
HcY7irB8mR3ajdzjUZLBQEMktp096Nheq3U75A==

`pragma protect key_keyowner="Synplicity", key_keyname="SYNP15_1", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=256)
`pragma protect key_block
hpeBLwN9x2ZFDwroYLlUe5GjjDepHik2l0c2s3/6S7JPCRkzQSyt2V1Ad/JewAs/QNp5SXSbYYB4
rQl0My1LDMF3xw43r0g2IbcyHVpPhGp0W5msuQdF67afnsRv90iJYWLMI3QkYGCTWAzl4HrLxFSg
3z8XZRK670IcxznOrlvgHmIKsvubZrBkuc1EynrVb9Nw16QnIx2rc4WgcEXeFf+4i1RoYLDd3gXK
NFCNMdtaRYUThunFP6Z4ViZ5UnDmKq+IMhd31jTaqIlWOBDxPI1+v5RJYxIyTbn4rxlKR2fNbl5/
z4OUjBTd+1GH3I2OXlqmAOvIhpe2Z2HH7nZu/A==

`pragma protect key_keyowner="Mentor Graphics Corporation", key_keyname="MGC-PREC-RSA", key_method="rsa"
`pragma protect encoding = (enctype="BASE64", line_length=76, bytes=256)
`pragma protect key_block
Mt2RhTSUwEIEWeNARbyL+EdfS1UF6nPaL/fKl/7oO2gina93egwCWDLl1fbBtkfaPco0cu4MJ9K3
OraAsyHRlY+MNShmJ1LzAIA1LjZx4y55lu9dlQqSUXR7AW7wVbkg1864mK+hM/1XygU0jvebKNW9
B7xSER+asLO6pxi0mt7uC2PHxLPAYEszFhmnap82TtbDGdQ2qtyekY+ngs+N2fAdsblxVwJruiMl
e6XJ127M8N1mYwhWU2HtRpBOSnnKoHgD9fG51XK/rhk8DxT66QnX9uLPB+H25eDupBJGi1Y5o6x8
hOwZiSUVlBLh7brfzevh7+eRn+7es6wBas0+3w==

`pragma protect data_method = "AES128-CBC"
`pragma protect encoding = (enctype = "BASE64", line_length = 76, bytes = 87296)
`pragma protect data_block
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
7XFJuKZ68YgbVqkCeELmb0qZmucXRDJGS+32jmU=
`pragma protect end_protected
`ifndef GLBL
`define GLBL
`timescale  1 ps / 1 ps

module glbl ();

    parameter ROC_WIDTH = 100000;
    parameter TOC_WIDTH = 0;
    parameter GRES_WIDTH = 10000;
    parameter GRES_START = 10000;

//--------   STARTUP Globals --------------
    wire GSR;
    wire GTS;
    wire GWE;
    wire PRLD;
    wire GRESTORE;
    tri1 p_up_tmp;
    tri (weak1, strong0) PLL_LOCKG = p_up_tmp;

    wire PROGB_GLBL;
    wire CCLKO_GLBL;
    wire FCSBO_GLBL;
    wire [3:0] DO_GLBL;
    wire [3:0] DI_GLBL;
   
    reg GSR_int;
    reg GTS_int;
    reg PRLD_int;
    reg GRESTORE_int;

//--------   JTAG Globals --------------
    wire JTAG_TDO_GLBL;
    wire JTAG_TCK_GLBL;
    wire JTAG_TDI_GLBL;
    wire JTAG_TMS_GLBL;
    wire JTAG_TRST_GLBL;

    reg JTAG_CAPTURE_GLBL;
    reg JTAG_RESET_GLBL;
    reg JTAG_SHIFT_GLBL;
    reg JTAG_UPDATE_GLBL;
    reg JTAG_RUNTEST_GLBL;

    reg JTAG_SEL1_GLBL = 0;
    reg JTAG_SEL2_GLBL = 0 ;
    reg JTAG_SEL3_GLBL = 0;
    reg JTAG_SEL4_GLBL = 0;

    reg JTAG_USER_TDO1_GLBL = 1'bz;
    reg JTAG_USER_TDO2_GLBL = 1'bz;
    reg JTAG_USER_TDO3_GLBL = 1'bz;
    reg JTAG_USER_TDO4_GLBL = 1'bz;

    assign (strong1, weak0) GSR = GSR_int;
    assign (strong1, weak0) GTS = GTS_int;
    assign (weak1, weak0) PRLD = PRLD_int;
    assign (strong1, weak0) GRESTORE = GRESTORE_int;

    initial begin
	GSR_int = 1'b1;
	PRLD_int = 1'b1;
	#(ROC_WIDTH)
	GSR_int = 1'b0;
	PRLD_int = 1'b0;
    end

    initial begin
	GTS_int = 1'b1;
	#(TOC_WIDTH)
	GTS_int = 1'b0;
    end

    initial begin 
	GRESTORE_int = 1'b0;
	#(GRES_START);
	GRESTORE_int = 1'b1;
	#(GRES_WIDTH);
	GRESTORE_int = 1'b0;
    end

endmodule
`endif
