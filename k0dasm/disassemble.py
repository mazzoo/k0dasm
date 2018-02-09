import sys
import unittest


def disassemble(mem, pc):
    # nop                         ;00
    if mem[0] == 0x00:
        return ("NOP", pc+1)

    # not1 cy                     ;01
    elif mem[0] == 0x01:
        return ('NOT1 CY', pc+1)

    # movw ax,!0abceh             ;02 CE AB       saddrp TODO is this really saddrp?
    elif mem[0] == 0x02:
        saddrp = mem[1] + (mem[2] << 8)
        return ('MOVW AX,!0%04xH' % saddrp, pc+3)

    # MOVW !0abceh,AX             ;03 CE AB       saddrp TODO is this really saddrp?
    elif mem[0] == 0x03:
        saddrp = mem[1] + (mem[2] << 8)
        return ('MOVW !0%04xH,AX' % saddrp, pc+3)

    # DBNZ 0fe20h,$label0         ;04 20 FD       saddr
    elif mem[0] == 0x04:
        saddr = _saddr(mem[1])
        disp = mem[2]
        # TODO calculate pc from displacement
        return ('DBNZ 0%04xH,$disp=%02x' % (saddr, disp), pc+3)

    # XCH A,[DE]
    elif mem[0] == 0x05:
        return ("XCH A,[DE]", pc+1)

    # ILLEGAL
    elif mem[0] == 0x06:
        return ("ILLEGAL 0x06", pc+1)

    # 'XCH A,[HL]'
    elif mem[0] == 0x07:
        return ('XCH A,[HL]', pc+1)

    # ADD A,!0abcdh               ;08 CD AB
    elif mem[0] == 0x08:
        addr16 = mem[1] + (mem[2] << 8)
        return ("ADD A,!0%04xh" % addr16, pc+3)

    # ADD A,[HL+0abh]             ;09 AB
    elif mem[0] == 0x09:
        byte = mem[1]
        return ("ADD A,[HL+%02xH]" % byte, pc+2)

    # callt [0040H]               ;C1
    # CALLT [{addr5}]             0b11ttttt1                            1
    elif (mem[0] & 0b11000001) == 0b11000001:
        offset = (mem[0] & 0b00111110) >> 1
        addr5 = 0x40 + (offset * 2)
        return ("CALLT [%04xH]" % addr5, pc+1)

    # callf !0800h                ;0C 00          0c = callf 0800h-08ffh
    # CALLF !{addr11}             0b0xxx1100         0bffffffff         2
    elif (mem[0] & 0b10001111) == 0b00001100:
        base = 0x0800 + ((mem[0] >> 4) << 8)
        address = base + mem[1]
        return ("CALLF !%04xH" % address, pc+2)

    # 0x0d: 'ADD A,#byte'
    # ADD A,#0abh                 ;0D AB
    elif mem[0] == 0x0d:
        byte = mem[1]
        return ('ADD A,#0%02xH' % byte, pc+2)

    # 0x0e: 'ADD A,saddr'
    # ADD A,0fe20h                ;0E 20          saddr
    elif mem[0] == 0x0e:
        saddr = _saddr(mem[1])
        return ('ADD A,0%04xH' % saddr, pc+2)

    # 0x0f: 'ADD A,[HL]'
    # ADD A,[HL]                  ;0F
    elif mem[0] == 0x0f:
        return ('ADD A,[HL]', pc+1)

    # 0x10: 'MOVW AX,#word'
    # MOVW AX,#0abcdh             ;10 CD AB
    elif mem[0] == 0x10:
        imm16 = mem[1] + (mem[2] << 8)
        return ('MOVW AX,#0%04xH' % imm16, pc+3)

    # 0x15: ILLEGAL
    elif mem[0] == 0x15:
        return ("ILLEGAL 0x15", pc+1)

    # 0x17: ILLEGAL
    elif mem[0] == 0x17:
        return ("ILLEGAL 0x17", pc+1)

    # 0x20: 'SET1 CY'
    elif mem[0] == 0x20:
        return ('SET1 CY', pc+1)

    # 0x21: 'CLR1 CY'
    elif mem[0] == 0x21:
        return ('CLR1 CY', pc+1)

    # 0x22: 'PUSH PSW'
    elif mem[0] == 0x22:
        return ('PUSH PSW', pc+1)

    # 0x23: 'POP PSW'
    elif mem[0] == 0x23:
        return ('POP PSW', pc+1)

    # 0x30: 'XCH A,X' .. 0x37: 'XCH A,H'
    elif (mem[0] & 0b11111000) == 0b00110000:
        reg = mem[0] & 0b111
        regname = _regname(reg)
        return ("XCH A,%s" % regname, pc+1)

    # 0x40: 'INC X' .. 0x47: 'INC H'
    elif (mem[0] & 0b11111000) == 0b01000000:
        reg = mem[0] & 0b111
        regname = _regname(reg)
        return ("INC %s" % regname, pc+1)

    # 0x50: 'DEC X' .. 0x57: 'DEC H'
    elif (mem[0] & 0b11111000) == 0b01010000:
        reg = mem[0] & 0b111
        regname = _regname(reg)
        return ("DEC %s" % regname, pc+1)

    # 0x60: 'MOV A,X' .. 0x67: 'MOV A,H'
    elif (mem[0] & 0b11111000) == 0b01100000:
        reg = mem[0] & 0b111
        regname = _regname(reg)
        return ("MOV A,%s" % regname, pc+1)

    # 0x70: 'MOV X,A' .. 0x77: 'MOV H,A'
    elif (mem[0] & 0b11111000) == 0b01110000:
        reg = mem[0] & 0b111
        regname = _regname(reg)
        return ("MOV %s,A" % regname, pc+1)

    # 0x80, 0x82, 0x84, 0x86
    elif (mem[0] & 0b11111001) == 0b10000000:
        regpair = (mem[0] >> 1) & 0b11
        regpairname = _regpairname(regpair)
        return ("INCW %s" % regpairname, pc+1)

    # 0x81: 'INC saddr'
    # INC 0fe20h                  ;81 20          saddr
    elif mem[0] == 0x81:
        saddr = _saddr(mem[1])
        return ('INC 0%04xH' % saddr, pc+2)

    elif mem[0] == 0x8f:
        return ("RETI", pc+1)

    # 0x90, 0x92, 0x94, 0x96
    elif (mem[0] & 0b11111001) == 0b10010000:
        regpair = (mem[0] >> 1) & 0b11
        regpairname = _regpairname(regpair)
        return ("DECW %s" % regpairname, pc+1)

    # 0x91: 'DEC saddr'
    # DEC 0fe20h                  ;91 20          saddr
    elif mem[0] == 0x91:
        saddr = _saddr(mem[1])
        return ('DEC 0%04xH' % saddr, pc+2)

    # 0x9a: 'CALL !addr16'
    elif mem[0] == 0x9a:
        addr16 = mem[1] + (mem[2] << 8)
        return ('CALL !0%04xH' % addr16, pc+3)

    # 0x9b: 'BR !addr16'
    elif mem[0] == 0x9b:
        addr16 = mem[1] + (mem[2] << 8)
        return ('BR !0%04xH' % addr16, pc+3)

    elif mem[0] == 0x9f:
        return ("RETB", pc+1)

    # 0xa0: 'MOV X,#byte' .. 0xa7: 'MOV H,#byte'
    elif (mem[0] & 0b11111000) == 0b10100000:
        reg = mem[0] & 0b111
        regname = _regname(reg)
        byte = mem[1]
        return ("MOV %s,#0%02xH" % (regname, byte), pc+1)

    elif mem[0] == 0xaf:
        return ("RET", pc+1)

    # 0xB0, 0xB2, 0xB4, 0xB6
    elif (mem[0] & 0b11111001) == 0b10110000:
        regpair = (mem[0] >> 1) & 0b11
        regpairname = _regpairname(regpair)
        return ("POP %s" % regpairname, pc+1)

    # 0xB1, 0xB3, 0xB5, 0xB7
    elif (mem[0] & 0b11111001) == 0b10110001:
        regpair = (mem[0] >> 1) & 0b11
        regpairname = _regpairname(regpair)
        return ("PUSH %s" % regpairname, pc+1)

    # 0xba: 'MOV [HL+C],A'
    # MOV [HL+C],A                ;BA
    elif mem[0] == 0xba:
        return ("MOV [HL+C],A", 1)

    # MOV [HL+B],A                ;BB
    elif mem[0] == 0xbb:
        return ("MOV [HL+B],A", 1)

    elif mem[0] == 0xbf:
        return ("BRK", pc+1)

    # 0xC0, 0xC2, 0xC4, 0xC6
    elif (mem[0] & 0b11111001) == 0b11000000:
        # TODO emit ILLEGAL for 0xC0
        regpair = (mem[0] >> 1) & 0b11
        regpairname = _regpairname(regpair)
        return ("MOVW AX,%s" % regpairname, pc+1)

    # 0xD0, 0xD2, 0xD4, 0xD6
    elif (mem[0] & 0b11111001) == 0b11010000:
        # TODO emit ILLEGAL for 0xD0
        regpair = (mem[0] >> 1) & 0b11
        regpairname = _regpairname(regpair)
        return ("MOVW %s,AX" % regpairname, pc+1)

    # 0xE0, 0xE2, 0xE4, 0xE6
    elif (mem[0] & 0b11111001) == 0b11100000:
        # TODO emit ILLEGAL for 0xD0
        regpair = (mem[0] >> 1) & 0b11
        regpairname = _regpairname(regpair)
        return ("XCHW AX,%s" % regpairname, pc+1)

    else:
        raise NotImplementedError()


def _regpairname(regpair):
    return ('AX', 'BC', 'DE', 'HL')[regpair]

def _regname(reg):
    return ('X', 'A', 'C', 'B', 'E', 'D', 'L', 'H')[reg]

def _saddr(byte):
    # When 8-bit immediate data is at 20H to FFH,
    # bit 8 of an effective address is set to 0. When
    # it is at 00H to 1FH, bit 8 is set to 1.
    saddr = 0xfe00 + byte
    if byte in range(0x20):
        saddr |= 0b100000000
    return saddr


class disassemble_tests(unittest.TestCase):
    def test_00_nop(self):
        mem = [0x00]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "NOP")
        self.assertEqual(new_pc, 1)

    def test_01_not1_cy1(self):
        mem = [0x01]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "NOT1 CY")
        self.assertEqual(new_pc, 1)

    def test_02_movw_ax_saddrp(self):
        mem = [0x02, 0xce, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOVW AX,!0abceH")
        self.assertEqual(new_pc, 3)

    def test_03_movw_saddrp_ax(self):
        mem = [0x03, 0xce, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOVW !0abceH,AX")
        self.assertEqual(new_pc, 3)

    def test_04_dbnz_saddr_disp(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x04, saddr_low, 0xFD]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "DBNZ 0%04xH,$disp=fd" % saddr)
            self.assertEqual(new_pc, 3)

    def test_05_xch_a_de(self):
        mem = [0x05]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "XCH A,[DE]")
        self.assertEqual(new_pc, 1)

    def test_06_illegal(self):
        mem = [0x06]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "ILLEGAL 0x06")
        self.assertEqual(new_pc, 1)

    def test_07_xch_a_hl(self):
        mem = [0x07]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "XCH A,[HL]")
        self.assertEqual(new_pc, 1)

    def test_08_add_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x08, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "ADD A,!0%04xh" % addr16)
            self.assertEqual(new_pc, 3)

    def test_09_add_a_hl_plus_byte(self):
        for byte in (0x00, 0xab, 0xff):
            mem = [0x09, byte]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "ADD A,[HL+%02xH]" % byte)
            self.assertEqual(new_pc, 2)

    def test_callf(self):
        d = {0x0C: 0x0800, 0x1C: 0x0900, 0x2C: 0x0A00, 0x3C: 0x0B00,
             0x4C: 0x0C00, 0x5C: 0x0D00, 0x6C: 0x0E00, 0x7C: 0x0F00}

        for opcode, base in d.items():
            for offset in (0x00, 0xab, 0xff):
                mem = [opcode, offset]
                disasm, new_pc = disassemble(mem, pc=0)
                address = base + offset
                self.assertEqual(disasm, "CALLF !%04xH" % address)
                self.assertEqual(new_pc, 2)

    def test_callt(self):
        d = {0xC1: 0x0040, 0xC3: 0x0042, 0xC5: 0x0044, 0xC7: 0x0046,
             0xC9: 0x0048, 0xCB: 0x004a, 0xCD: 0x004c, 0xCF: 0x004e,
             0xD1: 0x0050, 0xD3: 0x0052, 0xD5: 0x0054, 0xD7: 0x0056,
             0xD9: 0x0058, 0xDB: 0x005A, 0xDD: 0x005C, 0xDF: 0x005e,
             0xE1: 0x0060, 0xE3: 0x0062, 0xE5: 0x0064, 0xE7: 0x0066,
             0xE9: 0x0068, 0xEB: 0x006a, 0xED: 0x006c, 0xEF: 0x006e,
             0xF1: 0x0070, 0xF3: 0x0072, 0xF5: 0x0074, 0xF7: 0x0076,
             0xF9: 0x0078, 0xFB: 0x007a, 0xFD: 0x007c, 0xFF: 0x007e,
            }

        for opcode, address in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "CALLT [%04xH]" % address)
            self.assertEqual(new_pc, 1)

    def test_0d_add_a_imm(self):
        for byte in (0, 0xab, 0xff):
            mem = [0x0d, byte]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'ADD A,#0%02xH' % byte)
            self.assertEqual(new_pc, 2)

    def test_0e_addr_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x0e, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'ADD A,0%04xH' % saddr)
            self.assertEqual(new_pc, 2)

    def test_0f_add_a_hl(self):
        mem = [0x0f]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'ADD A,[HL]')
        self.assertEqual(new_pc, 1)

    def test_10_movw_ax_imm16(self):
        for imm16 in (0x0000, 0xabcd, 0xffff):
            low = imm16 & 0xff
            high = (imm16 >> 8) & 0xff
            mem = [0x10, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'MOVW AX,#0%04xH' % imm16)
            self.assertEqual(new_pc, 3)

    def test_15_illegal(self):
        mem = [0x15]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "ILLEGAL 0x15")
        self.assertEqual(new_pc, 1)

    def test_17_illegal(self):
        mem = [0x17]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "ILLEGAL 0x17")
        self.assertEqual(new_pc, 1)

    def test_20_set1_cy(self):
        mem = [0x20]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "SET1 CY")
        self.assertEqual(new_pc, 1)

    def test_21_clr1_cy(self):
        mem = [0x21]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "CLR1 CY")
        self.assertEqual(new_pc, 1)

    def test_22_push_psw(self):
        mem = [0x22]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "PUSH PSW")
        self.assertEqual(new_pc, 1)

    def test_23_pop_psw(self):
        mem = [0x23]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "POP PSW")
        self.assertEqual(new_pc, 1)

    def test_30_37_xch_a_reg(self):
        d = {0x30: 'XCH A,X', 0x31: 'XCH A,A', 0x32: 'XCH A,C',
             0x33: 'XCH A,B', 0x34: 'XCH A,E', 0x35: 'XCH A,D',
             0x36: 'XCH A,L', 0x37: 'XCH A,H'}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_40_47_inc_reg(self):
        d = {0x40: 'INC X', 0x41: 'INC A', 0x42: 'INC C',
             0x43: 'INC B', 0x44: 'INC E', 0x45: 'INC D',
             0x46: 'INC L', 0x47: 'INC H'}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_50_57_dec_reg(self):
        d = {0x50: 'DEC X', 0x51: 'DEC A', 0x52: 'DEC C',
             0x53: 'DEC B', 0x54: 'DEC E', 0x55: 'DEC D',
             0x56: 'DEC L', 0x57: 'DEC H'}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_60_67_mov_a_reg(self):
        d = {0x60: 'MOV A,X', 0x61: 'MOV A,A', 0x62: 'MOV A,C',
             0x63: 'MOV A,B', 0x64: 'MOV A,E', 0x65: 'MOV A,D',
             0x66: 'MOV A,L', 0x67: 'MOV A,H'}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_70_77_mov_a_reg(self):
        d = {0x70: 'MOV X,A', 0x71: 'MOV A,A', 0x72: 'MOV C,A',
             0x73: 'MOV B,A', 0x74: 'MOV E,A', 0x75: 'MOV D,A',
             0x76: 'MOV L,A', 0x77: 'MOV H,A'}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_80_82_84_86_incw_regpair(self):
        d = {0x80: "INCW AX", 0x82: "INCW BC",
             0x84: "INCW DE", 0x86: "INCW HL"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_81_inc_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x81, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "INC 0%04xH" % saddr)
            self.assertEqual(new_pc, 2)

    def test_8f_reti(self):
        mem = [0x8f]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "RETI")
        self.assertEqual(new_pc, 1)

    def test_90_92_94_96_decw_regpair(self):
        d = {0x90: "DECW AX", 0x92: "DECW BC",
             0x94: "DECW DE", 0x96: "DECW HL"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_91_dec_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x91, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "DEC 0%04xH" % saddr)
            self.assertEqual(new_pc, 2)

    def test_9a_call_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x9a, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'CALL !0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_9b_br_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x9b, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'BR !0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_9f_retb(self):
        mem = [0x9F]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "RETB")
        self.assertEqual(new_pc, 1)

    def test_a0_a7_mov_reg_imm8(self):
        d = {0xa0: 'MOV X,#0%02xH', 0xa1: 'MOV A,#0%02xH',
             0xa2: 'MOV C,#0%02xH', 0xa3: 'MOV B,#0%02xH',
             0xa4: 'MOV E,#0%02xH', 0xa5: 'MOV D,#0%02xH',
             0xa6: 'MOV L,#0%02xH', 0xa7: 'MOV H,#0%02xH'}

        for opcode, expected_disasm_fmt in d.items():
            for imm8 in (0x00, 0xab, 0xff):
                mem = [opcode, imm8]
                disasm, new_pc = disassemble(mem, pc=0)
                self.assertEqual(disasm, expected_disasm_fmt % imm8)
                self.assertEqual(new_pc, 1)

    def test_af_ret(self):
        mem = [0xAF]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "RET")
        self.assertEqual(new_pc, 1)

    def test_b0_b2_b4_b6_pop_regpair(self):
        d = {0xB0: "POP AX", 0xB2: "POP BC",
             0xB4: "POP DE", 0xB6: "POP HL"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_b1_b3_b5_b7_push_regpair(self):
        d = {0xB1: "PUSH AX", 0xB3: "PUSH BC",
             0xB5: "PUSH DE", 0xB7: "PUSH HL"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_ba_mov_hl_plus_c_a(self):
        mem = [0xBA]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV [HL+C],A")
        self.assertEqual(new_pc, 1)

    def test_bb_mov_hl_plus_b_a(self):
        mem = [0xBB]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV [HL+B],A")
        self.assertEqual(new_pc, 1)

    def test_bf_brk(self):
        mem = [0xBF]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "BRK")
        self.assertEqual(new_pc, 1)

    def test_c2_c4_c6_mov_ax_regpair(self):
        d = {0xC2: "MOVW AX,BC", 0xC4: "MOVW AX,DE", 0xC6: "MOVW AX,HL"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_d2_d4_d6_mov_regpair(self):
        d = {0xD2: "MOVW BC,AX", 0xD4: "MOVW DE,AX", 0xD6: "MOVW HL,AX"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_e2_e4_e6_xchw_ax_regpair(self):
        d = {0xE2: "XCHW AX,BC", 0xE4: "XCHW AX,DE", 0xE6: "XCHW AX,HL"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
