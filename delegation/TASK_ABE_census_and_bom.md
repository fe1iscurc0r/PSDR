# TASKS A/B/E - every distinct part on the board, and the DigiKey-numbered BOM rows

A = lifecycle status per line, B = LCSC/SMT usability, E = the official
datasheet URL + revision + page for each part type you are asked about.

## 1. part census (part_type, qty, category, designators)

Passive part-type names encode the value, e.g.
`CSM-X5R-22U-20P-10V-1210` = 22 uF X5R 20% 10 V 1210,
`RSM-6K98-1PCT-250MW-1206` = 6.98 kOhm 1% 250 mW 1206.

```csv
part_type,qty,category,designators
CAP_0603,130,passive,"C10,C110,C111,C115,C118,C119,C120,C123,C125,C129,C13,C132,C134,C135,C137,C139,C148,C149,C157,C159,C160,C17,C171,C173,...(of 130)"
RES_0603,104,passive,"R1,R112,R113,R116,R117,R12,R122,R124,R127,R128,R130,R133,R136,R14,R140,R144,R145,R146,R150,R162,R164,R165,R167,R168,...(of 104)"
PAD_1MM,33,ic_or_other,"1/2VCC,1PPS,3V3A,3V3D,5VBST,BIAS,CLKA,CLKB,DAC1,DAC2,DUT,EAR,GND,GPSR,GPSRX,GPSTX,LIPO,LO1N,LO1P,LO2N,LO2P,MAG,MIC,PHSE,...(of 33)"
CSM-X5R-22U-20P-10V-1210,11,passive,"C142,C143,C151,C152,C154,C158,C163,C323,C326,C42,C43"
"0.1""_1PIN",9,ic_or_other,"+,-,CLK,E_FILT_IF_N,E_FILT_IF_P,E_FILT_RF_N,E_FILT_RF_P,IO,NRST"
CAP_0805,7,passive,"C103,C104,C106,C107,C108,C156,C89"
CSM-X5R-10U0-10P-25V-0805,7,passive,"C147,C155,C188,C191,C192,C247,C258"
FIDUCIAL_1MM,6,ic_or_other,"F1,F2,F3,F4,F5,F6"
MOSFET_P_SOT23_IRLML6401,5,ic_or_other,"Q126,Q178,Q208,Q246,Q5"
OP_AMP_FAN4174,5,ic_or_other,"U131,U216,U227,U47,U58"
MH3M,4,ic_or_other,"M4,M5,M6,M7"
DPDT_ANALOG_MAX4525,3,ic_or_other,"U18,U4,U86"
ISM-0805-10U,3,passive,"L105,L141,L34"
LED_0603,3,ic_or_other,"D100,D101,D102"
MH3M_PLATED,3,ic_or_other,"M1,M2,M3"
RF_DPDT_MASWSS0129TR,3,ic_or_other,"U16,U24,U30"
RSM-6K98-1PCT-250MW-1206,3,passive,"R22,R23,R25"
74CBTLV3253,2,ic_or_other,"U211,U298"
AD8131,2,ic_or_other,"U253,U260"
BALUN_1-2_WBC2-1TL,2,ic_or_other,"L39,L82"
BUTTON_B3U-1000P-B,2,ic_or_other,"BOOT,RST"
CRYSTAL3225,2,ic_or_other,"Y182,Y237"
IND_SMT_220UH_SRN4018-221M,2,passive,"L11,L19"
MCP6N11,2,ic_or_other,"U255,U272"
MH_80M,2,ic_or_other,"X1,X2"
MIXER_DIODE-RING_ADE-2ASK,2,ic_or_other,"L41,L81"
MORSE_PADDLE_CONTACTS,2,ic_or_other,"CW1,CW2"
SMA_BOARD_EDGE,2,ic_or_other,"ANT/VNA-IN,VNA-OUT"
SY10EP52V,2,ic_or_other,"U279,U280"
"0.1""_6P_HEADER_DUAL_ENTRY_1241152-6",1,ic_or_other,J153
2U2H_INDUCTOR_NR6028T2R2N,1,ic_or_other,L109
3.5MM_PHONO_4P_3SW_SJ-42617-SMT,1,ic_or_other,EARPHONE
3V3_LDO_MCP1802,1,ic_or_other,U172
AD8302,1,ic_or_other,U314
AUDIO_AMP_TPA0253DGQR,1,ic_or_other,U199
BAT-MANAGE_MCP73871,1,ic_or_other,U161
BOOST_REG_ADP1613,1,ic_or_other,U85
BUCK_REGULATOR_AP3417C,1,ic_or_other,U114
CRYSTAL_SMT_32.768,1,ic_or_other,Y183
CSM-X5R-10U0-10P-10V-0805,1,passive,C83
CSM-X5R-47U-20P-6V3-0805,1,passive,C301
DIGITAL_POT_MAX5388,1,ic_or_other,U15
DIODE-SMA,1,ic_or_other,D44
GPS_ANTENNA-W3062A,1,ic_or_other,GPS_ANTENNA
GPS_MODULE_RXM-GPS-RM-T,1,ic_or_other,U185
IND_4.7UH_SMT_CDRH4D28CNP-4R7PC,1,passive,L84
MICROPHONE_MEMS_SPU0410HR5H-PB,1,ic_or_other,U32
MICROSD_DM3CS-SF,1,ic_or_other,MICROSD
MICROUSB_H12192CT-ND,1,ic_or_other,USB
MIC_PREAMP_SSM2167,1,ic_or_other,U189
MMIC-AMP_HMC482ST,1,ic_or_other,U304
SI5338,1,ic_or_other,U241
SPDT_ANALOG_SWITCH_SN74LVC1G3157,1,ic_or_other,U37
SPEAKER_SMT_WATERPROOF_2403-260-00107,1,ic_or_other,SPEAKER
SPI_LCD_BOTTOM_ENTRY,1,ic_or_other,J170
STM32F746_LQFP100,1,ic_or_other,U121
VARIABLE_FILTER_HMC1023,1,ic_or_other,U287
```

## 2. BOM rows that carry a DigiKey number

```csv
qty,digikey,vendor,mpn,octopart_url
Qty,Line Item,Manufacturer,MPN,Octopart URL
2,WM50018-05-ND,Molex,22-28-4054,https://octopart.com/22-28-4054-molex-278278
2,J629-ND,Emerson Network Power,142-0711-821,https://octopart.com/142-0711-821-emerson+network+power-39448276
2,SW1143CT-ND,Omron,B3U-1000P-B,https://octopart.com/b3u-1000p-b-omron-1057356
68,490-3285-1-ND,Murata,GRM188R72A104KA35D,https://octopart.com/grm188r72a104ka35d-murata-196904
4,1276-1008-1-ND,Samsung,CL10C101JB8NNNC,https://octopart.com/cl10c101jb8nnnc-samsung-9299377
5,1276-1009-1-ND,Samsung,CL10B103KB8NNNC,https://octopart.com/cl10b103kb8nnnc-samsung-9299374
15,1276-1113-1-ND,Samsung,CL21B106KQQNNNE,https://octopart.com/cl21b106kqqnnne-samsung-18183217
15,490-1472-1-ND,Murata,GRM188R72A102KA01D,https://octopart.com/grm188r72a102ka01d-murata-196190
7,1276-1946-1-ND,Samsung,CL10B105KP8NNNC,https://octopart.com/cl10b105kp8nnnc-samsung-19831604
11,1276-3375-1-ND,Samsung,CL32A227MQVNNNE,https://octopart.com/cl32a227mqvnnne-samsung-21642163
4,1276-1193-1-ND,Samsung,CL10A226MQ8NRNC,https://octopart.com/cl10a226mq8nrnc-samsung-19018972
5,1276-1134-1-ND,Samsung,CL10B225KP8NNNC,https://octopart.com/cl10b225kp8nnnc-samsung-19831669
1,1276-2030-1-ND,Samsung,CL10B332JB8NNNC,https://octopart.com/cl10b332jb8nnnc-samsung-15492529
1,311-4001-1-ND,Yageo,CC0603JRX7R8BB333,https://octopart.com/cc0603jrx7r8bb333-yageo-25629527
4,1276-1062-1-ND,Samsung,CL10B474KO8NNNC,https://octopart.com/cl10b474ko8nnnc-samsung-9301678
1,1276-2420-1-ND,Samsung,CL21A476MQCLRNC,https://octopart.com/cl21a476mqclrnc-samsung-24871259
4,490-7203-1-ND,Murata,GRM188R61E475KE11D,https://octopart.com/grm188r61e475ke11d-murata-26982327
2,1276-2133-1-ND,Samsung,CL10C060CB8NNNC,https://octopart.com/cl10c060cb8nnnc-samsung-19831802
5,445-14209-1-ND,TDK,C1608X6S1A685K080AC,https://octopart.com/c1608x6s1a685k080ac-tdk-28168623
2,445-14102-1-ND,TDK,C1608NP02A080D080AA,https://octopart.com/c1608np02a080d080aa-tdk-28168516
1,475-2831-1-ND,Osram Opto,LW Q38E-Q1OO-3K6L-1,https://octopart.com/lw+q38e-q1oo-3k6l-1-osram+opto-61925015
1,475-2512-1-ND,Osram Opto,LS Q976-NR-1,https://octopart.com/ls+q976-nr-1-osram+opto-31093944
1,511-1577-1-ND,rohm,SML-D12D8WT86,https://octopart.com/sml-d12d8wt86-rohm-9290841
1,MBRA340T3GOSCT-ND,ON Semiconductor,MBRA340T3G,https://octopart.com/mbra340t3g-on+semiconductor-330950
1,CP-43617SJCT-ND,CUI Devices,SJ-43617-SMT-TR,https://octopart.com/sj-43617-smt-tr-cui+devices-106234256
1,553-2579-1-ND,Pulse,W3062A,https://octopart.com/w3062a-pulse-20005248
1,A107015CT-ND,TE Connectivity,1241152-6,https://octopart.com/1241152-6-te+connectivity-41017930
1,A107013CT-ND,TE Connectivity,1-1241152-0,https://octopart.com/1-1241152-0-te+connectivity-40985157
3,445-173012-1-ND,TDK,VLS201612HBX-2R2M-1,https://octopart.com/vls201612hbx-2r2m-1-tdk-52458620
1,587-2098-1-ND,Taiyo Yuden,NR6028T2R2N,https://octopart.com/nr6028t2r2n-taiyo+yuden-8598465
2,WBC2-1TLB,Coilcraft,WBC2-1TLB,https://octopart.com/wbc2-1tlb-coilcraft-6747758
1,308-2043-1-ND,Sumida,CDRH4D28CNP-4R7PC,https://octopart.com/cdrh4d28cnp-4r7pc-sumida-11543079
2,SRN4018-221MCT-ND,Bourns,SRN4018-221M,https://octopart.com/srn4018-221m-bourns-25452390
2,ADE-2ASK,Mini-Circuits,ADE2ASK+,https://octopart.com/ade2ask%2B-mini-circuits-64850656
1,HR1972CT-ND,Hirose,DM3CS-SF,https://octopart.com/dm3cs-sf-hirose-44525751
5,IRLML6401PBFCT-ND,Infineon,IRLML6401TRPBF,https://octopart.com/irlml6401trpbf-infineon-65874987
11,541-0.0GCT-ND,Vishay,CRCW06030000Z0EA,https://octopart.com/crcw06030000z0ea-vishay-39556096
25,P100KGCT-ND,Panasonic,ERJ-3GEYJ104V,https://octopart.com/erj-3geyj104v-panasonic-55421973
1,P100GCT-ND,Panasonic,ERJ-3GEYJ101V,https://octopart.com/erj-3geyj101v-panasonic-55405017
1,RHM68DCT-ND,rohm,ESR03EZPJ680,https://octopart.com/esr03ezpj680-rohm-29236221
1,RHM180DCT-ND,rohm,ESR03EZPJ181,https://octopart.com/esr03ezpj181-rohm-19170366
15,MCT0603-10.0K-CFCT-ND,Vishay,MCT06030C1002FP500,https://octopart.com/mct06030c1002fp500-vishay-55388462
1,490-2436-1-ND,Murata,NCP18XH103J03RB,https://octopart.com/ncp18xh103j03rb-murata-745856
1,RHM10DCT-ND,rohm,ESR03EZPJ100,https://octopart.com/esr03ezpj100-rohm-19170060
4,1276-4751-1-ND,Samsung,RC1608F1212CS,https://octopart.com/rc1608f1212cs-samsung-9300780
1,MCT0603-15.0K-CFCT-ND,Vishay,MCT06030C1502FP500,https://octopart.com/mct06030c1502fp500-vishay-43439988
27,MCT0603-1.00K-CFCT-ND,Vishay,MCT06030C1001FP500,https://octopart.com/mct06030c1001fp500-vishay-46566501
2,311-22.1HRCT-ND,Yageo,RC0603FR-0722R1L,https://octopart.com/rc0603fr-0722r1l-yageo-1190988
2,1276-3499-1-ND,Samsung,RC1608F24R9CS,https://octopart.com/rc1608f24r9cs-samsung-21533637
3,P255HCT-ND,Panasonic,ERJ-3EKF2550V,https://octopart.com/erj-3ekf2550v-panasonic-55403658
1,311-240KHRCT-ND,Yageo,RC0603FR-07240KL,https://octopart.com/rc0603fr-07240kl-yageo-1210448
1,541-30.0KHCT-ND,Vishay,CRCW060330K0FKEA,https://octopart.com/crcw060330k0fkea-vishay-39843189
1,311-402KHRCT-ND,Yageo,RC0603FR-07402KL,https://octopart.com/rc0603fr-07402kl-yageo-1226024
2,1276-3505-1-ND,Samsung,RC1608F49R9CS,https://octopart.com/rc1608f49r9cs-samsung-10312292
3,1276-5659-1-ND,Samsung,RC3216F49R9CS,https://octopart.com/rc3216f49r9cs-samsung-19018360
1,541-4.99KHCT-ND,Vishay,CRCW06034K99FKEA,https://octopart.com/crcw06034k99fkea-vishay-39455801
1,P6.81KHCT-ND,Panasonic,ERJ-3EKF6811V,https://octopart.com/erj-3ekf6811v-panasonic-55421889
1,668-AS01508MO-SC11-R-ND,PUI Audio,AS01508MO-SC11-R,https://octopart.com/as01508mo-sc11-r-pui+audio-107482094
1,MCP1802T-3302I/OTCT-ND,Microchip,MCP1802T-3302I/OT,https://octopart.com/mcp1802t-3302i%2Fot-microchip-7503791
2,296-17283-1-ND,Texas Instruments,SN74CB3Q3253DBQR,https://octopart.com/sn74cb3q3253dbqr-texas+instruments-472364
2,AD8131ARMZ-ND,Analog Devices,AD8131ARMZ,https://octopart.com/ad8131armz-analog+devices-138565
1,AD8302ARUZ-ND,Analog Devices,AD8302ARUZ,https://octopart.com/ad8302aruz-analog+devices-541810
1,296-7006-1-ND,Texas Instruments,TPA0253DGQR,https://octopart.com/tpa0253dgqr-texas+instruments-407770
1,MCP73871-2AAI/ML-ND,Microchip,MCP73871-2AAI/ML,https://octopart.com/mcp73871-2aai%2Fml-microchip-8315795
1,ADP1613ARMZ-R7CT-ND,Analog Devices,ADP1613ARMZ-R7,https://octopart.com/adp1613armz-r7-analog+devices-11763485
1,AP3417CKTR-G1DICT-ND,Diodes Inc.,AP3417CKTR-G1,https://octopart.com/ap3417cktr-g1-diodes+inc.-30954683
1,MAX5388NAUB+-ND,Maxim Integrated,MAX5388NAUB+,https://octopart.com/max5388naub%2B-maxim+integrated-42866431
3,MAX4525CUB+-ND,Maxim Integrated,MAX4525CUB+,https://octopart.com/max4525cub%2B-maxim+integrated-42624946
1,RXM-GPS-RM-TCT-ND,Linx,RXM-GPS-RM-T,https://octopart.com/rxm-gps-rm-t-linx-31014155
2,MCP6N11-010E/SN-ND,Microchip,MCP6N11-010E/SN,https://octopart.com/mcp6n11-010e%2Fsn-microchip-20093814
1,SSM2167-1RMZ-R7CT-ND,Analog Devices,SSM2167-1RMZ-R7,https://octopart.com/ssm2167-1rmz-r7-analog+devices-12036810
1,423-1138-1-ND,Knowles Acoustics,SPU0410HR5H-PB,https://octopart.com/spu0410hr5h-pb-knowles+acoustics-19035281
1,599-1068-1-ND,RF Micro Devices (RFMD),SXB-2089Z,
5,FAN4174IS5XCT-ND,ON Semiconductor,FAN4174IS5X,https://octopart.com/fan4174is5x-on+semiconductor-84325058
3,1465-1374-1-ND,,MASWSS0129TR,
1,336-2552-ND,Silicon Labs,SI5338A-B-GM,https://octopart.com/si5338a-b-gm-silicon+labs-27547982
1,296-14909-1-ND,Texas Instruments,SN74LVC1G3157DCKR,https://octopart.com/sn74lvc1g3157dckr-texas+instruments-472291
1,497-15819-ND,STMicroelectronics,STM32F746VGT6,https://octopart.com/stm32f746vgt6-stmicroelectronics-59160106
2,MC10EP52DTGOS-ND,ON Semiconductor,MC10EP52DTG,https://octopart.com/mc10ep52dtg-on+semiconductor-461562
1,1127-1662-ND,Analog Devices,HMC1023LP5E,https://octopart.com/hmc1023lp5e-analog+devices-51966800
1,H12192CT-ND,Hirose,ZX62WRD-B-5PC,https://octopart.com/zx62wrd-b-5pc-hirose-25319682
2,SER3627CT-ND,Epson,TSX-3225 26.0000MF09Z-AC3,https://octopart.com/tsx-3225+26.0000mf09z-ac3-epson-44407668
1,535-11937-1-ND,Abracon,ABS07-120-32.768KHZ-T,https://octopart.com/abs07-120-32.768khz-t-abracon-24822702
1,455-1719-ND,JST,S2B-PH-K-S(LF)(SN),https://octopart.com/s2b-ph-k-s%28lf%29%28sn%29-jst-248883
1,PEC09-2320F-S0015-ND,Bourns,PEC09-2320F-S0015,https://octopart.com/pec09-2320f-s0015-bourns-19020381
```

## 3. non-passive part types (the datasheet target list)

- `0.1"_1PIN`
- `0.1"_6P_HEADER_DUAL_ENTRY_1241152-6`
- `2U2H_INDUCTOR_NR6028T2R2N`
- `3.5MM_PHONO_4P_3SW_SJ-42617-SMT`
- `3V3_LDO_MCP1802`
- `74CBTLV3253`
- `AD8131`
- `AD8302`
- `AUDIO_AMP_TPA0253DGQR`
- `BALUN_1-2_WBC2-1TL`
- `BAT-MANAGE_MCP73871`
- `BOOST_REG_ADP1613`
- `BUCK_REGULATOR_AP3417C`
- `BUTTON_B3U-1000P-B`
- `CRYSTAL3225`
- `CRYSTAL_SMT_32.768`
- `DIGITAL_POT_MAX5388`
- `DIODE-SMA`
- `DPDT_ANALOG_MAX4525`
- `FIDUCIAL_1MM`
- `GPS_ANTENNA-W3062A`
- `GPS_MODULE_RXM-GPS-RM-T`
- `LED_0603`
- `MCP6N11`
- `MH3M`
- `MH3M_PLATED`
- `MH_80M`
- `MICROPHONE_MEMS_SPU0410HR5H-PB`
- `MICROSD_DM3CS-SF`
- `MICROUSB_H12192CT-ND`
- `MIC_PREAMP_SSM2167`
- `MIXER_DIODE-RING_ADE-2ASK`
- `MMIC-AMP_HMC482ST`
- `MORSE_PADDLE_CONTACTS`
- `MOSFET_P_SOT23_IRLML6401`
- `OP_AMP_FAN4174`
- `PAD_1MM`
- `RF_DPDT_MASWSS0129TR`
- `SI5338`
- `SMA_BOARD_EDGE`
- `SPDT_ANALOG_SWITCH_SN74LVC1G3157`
- `SPEAKER_SMT_WATERPROOF_2403-260-00107`
- `SPI_LCD_BOTTOM_ENTRY`
- `STM32F746_LQFP100`
- `SY10EP52V`
- `VARIABLE_FILTER_HMC1023`

TOTALS: part_types=57 designators=391 non_passive_types=46
