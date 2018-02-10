import sys
import unittest
from disassemble import disassemble

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

    def test_10_12_14_16_movw_regpair_imm16(self):
        d = {0x10: "AX", 0x12: "BC", 0x14: "DE", 0x16: "HL"}

        for opcode, regpairname in d.items():
            for imm16 in (0x0000, 0xabcd, 0xffff):
                low = imm16 & 0xff
                high = (imm16 >> 8) & 0xff
                mem = [opcode, low, high]
                disasm, new_pc = disassemble(mem, pc=0)
                self.assertEqual(disasm, 'MOVW %s,#0%04xH' % (regpairname, imm16))
                self.assertEqual(new_pc, 3)

    def test_13_mov_sfr_imm8(self):
        for sfr in range(0xff00, 0x10000):
            sfr_low = sfr & 0xff
            mem = [0x13, sfr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "MOV 0%04xH,#0abH" % sfr)
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

    def test_18_sub_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x18, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'SUB A,!0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_19_sub_a_hl_plus_offset(self):
        mem = [0x19, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'SUB A,[HL+0abH]')
        self.assertEqual(new_pc, 2)

    def test_1d_sub_a_imm8(self):
        mem = [0x1d, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'SUB A,#0abH')
        self.assertEqual(new_pc, 1)

    def test_1e_sub_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x1e, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'SUB A,0%04xH' % saddr)
            self.assertEqual(new_pc, 2)

    def test_1f_sub_a_hl(self):
        mem = [0x1f]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "SUB A,[HL]")
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

    def test_24_ror_a(self):
        mem = [0x24]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "ROR A,1")
        self.assertEqual(new_pc, 1)

    def test_25_rorc_a(self):
        mem = [0x25]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "RORC A,1")
        self.assertEqual(new_pc, 1)

    def test_26_rol_a(self):
        mem = [0x26]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "ROL A,1")
        self.assertEqual(new_pc, 1)

    def test_27_rolc_a(self):
        mem = [0x27]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "ROLC A,1")
        self.assertEqual(new_pc, 1)

    def test_27_addc_a_hl(self):
        mem = [0x27]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "ROLC A,1")
        self.assertEqual(new_pc, 1)

    def test_28_addc_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x28, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'ADDC A,!0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_29_sub_a_hl_plus_offset(self):
        mem = [0x29, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'ADDC A,[HL+0abH]')
        self.assertEqual(new_pc, 2)

    def test_2d_a_imm8(self):
        mem = [0x2d, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "ADDC A,#0abH")
        self.assertEqual(new_pc, 1)

    def test_2e_addc_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x2e, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'ADDC A,0%04xH' % saddr)
            self.assertEqual(new_pc, 2)

    def test_30_37_xch_a_reg(self):
        d = {0x30: 'XCH A,X', 0x31: 'XCH A,A', 0x32: 'XCH A,C',
             0x33: 'XCH A,B', 0x34: 'XCH A,E', 0x35: 'XCH A,D',
             0x36: 'XCH A,L', 0x37: 'XCH A,H'}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_48_cmp_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x48, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'CMP A,!0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_39_subc_a_hl_plus_offset(self):
        mem = [0x39, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'SUBC A,[HL+0abH]')
        self.assertEqual(new_pc, 2)

    def test_3d_subc_a_imm8(self):
        mem = [0x3d, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "SUBC A,#0abH")
        self.assertEqual(new_pc, 2)

    def test_3e_subc_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x3e, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'SUBC A,0%04xH' % saddr)
            self.assertEqual(new_pc, 2)

    def test_3f_subc_a_hl(self):
        mem = [0x3f]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "SUBC A,[HL]")
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

    def test_49_cmp_a_hl_plus_offset(self):
        mem = [0x49, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'CMP A,[HL+0abH]')
        self.assertEqual(new_pc, 2)

    def test_4d_cmp_a_imm8(self):
        mem = [0x4d, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "CMP A,#0abH")
        self.assertEqual(new_pc, 2)

    def test_4e_cmp_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x4e, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'CMP A,0%04xH' % saddr)
            self.assertEqual(new_pc, 2)

    def test_4f_cmp_a_hl(self):
        mem = [0x4f]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "CMP A,[HL]")
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

    def test_58_and_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x58, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'AND A,!0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_59_and_a_hl_plus_offset(self):
        mem = [0x59, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'AND A,[HL+0abH]')
        self.assertEqual(new_pc, 2)

    def test_5d_and_a_imm8(self):
        mem = [0x5d, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "AND A,#0abH")
        self.assertEqual(new_pc, 2)

    def test_5e_and_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x5e, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'AND A,0%04xH' % saddr)
            self.assertEqual(new_pc, 2)

    def test_5f_and_a_hl(self):
        mem = [0x5f]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "AND A,[HL]")
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

    def test_68_or_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x68, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'OR A,!0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_69_or_a_hl_plus_offset(self):
        mem = [0x69, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'OR A,[HL+0abH]')
        self.assertEqual(new_pc, 2)

    def test_6d_or_a_imm8(self):
        mem = [0x6d, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "OR A,#0abH")
        self.assertEqual(new_pc, 2)

    def test_6e_or_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x6e, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'OR A,0%04xH' % saddr)
            self.assertEqual(new_pc, 2)

    def test_6f_or_a_hl(self):
        mem = [0x6f]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "OR A,[HL]")
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

    def test_78_xor_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x78, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'XOR A,!0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_79_xor_a_hl_plus_offset(self):
        mem = [0x79, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, 'XOR A,[HL+0abH]')
        self.assertEqual(new_pc, 2)

    def test_7d_xor_a_imm8(self):
        mem = [0x7d, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "XOR A,#0abH")
        self.assertEqual(new_pc, 1)

    def test_7e_xor_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x7e, saddr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'XOR A,0%04xH' % saddr)
            self.assertEqual(new_pc, 2)

    def test_7f_xor_a_hl(self):
        mem = [0x7f]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "XOR A,[HL]")
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

    def test_83_xch_a_saddr(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x83, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "XCH A,0%04xH" % saddr)
            self.assertEqual(new_pc, 2)

    def test_85_mov_a_de(self):
        mem = [0x85]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV A,[DE]")
        self.assertEqual(new_pc, 1)

    def test_87_mov_a_hl(self):
        mem = [0x87]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV A,[HL]")
        self.assertEqual(new_pc, 1)

    def test_88_add_saddr_imm8(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x88, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "ADD 0%04xH,#0abH" % saddr)
            self.assertEqual(new_pc, 3)

    def test_8a_bc_rel(self):
        mem = [0x8a, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "DBNZ C,$disp=ab")
        self.assertEqual(new_pc, 2)

    def test_8b_bc_rel(self):
        mem = [0x8b, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "DBNZ B,$disp=ab")
        self.assertEqual(new_pc, 2)

    def test_8e_mov_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x8e, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'MOV A,!0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

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

    def test_93_xch_a_sfr(self):
        for sfr in range(0xff00, 0x10000):
            sfr_low = sfr & 0xff
            mem = [0x93, sfr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "XCH A,0%04xH" % sfr)
            self.assertEqual(new_pc, 2)

    def test_95_mov_de_a(self):
        mem = [0x95]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV [DE],A")
        self.assertEqual(new_pc, 1)

    def test_97_mov_hl_a(self):
        mem = [0x97]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV [HL],A")
        self.assertEqual(new_pc, 1)

    def test_98_sub_saddr_imm8(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0x98, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "SUB 0%04xH,#0abH" % saddr)
            self.assertEqual(new_pc, 3)

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

    def test_9d_bnc_rel(self):
        mem = [0x9d, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "BNC $disp=ab")
        self.assertEqual(new_pc, 2)

    def test_9e_mov_addr16_a(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0x9e, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'MOV !0%04xH,A' % addr16)
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

    def test_a8_addc_saddr_imm8(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0xa8, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "ADDC 0%04xH,#0abH" % saddr)
            self.assertEqual(new_pc, 3)

    def test_a9_movw_ax_sfrp(self):
        for sfrp in range(0xff00, 0x10000, 2):
            sfrp_low = sfrp & 0xff
            mem = [0xa9, sfrp_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "MOVW AX,0%04xH" % sfrp)
            self.assertEqual(new_pc, 2)

    def test_aa_mov_a_hl_plus_c(self):
        mem = [0xaa]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV A,[HL+C]")
        self.assertEqual(new_pc, 1)

    def test_ab_mov_a_hl_plus_b(self):
        mem = [0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV A,[HL+B]")
        self.assertEqual(new_pc, 1)

    def test_ad_bz_rel(self):
        mem = [0xad, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "BZ $disp=ab")
        self.assertEqual(new_pc, 2)

    def test_ae_mov_a_hl_plus_byte(self):
        mem = [0xAE, 0xAB]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV A,[HL+0abH]")
        self.assertEqual(new_pc, 2)

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

    def test_b8_subc_saddr_imm8(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0xb8, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "SUBC 0%04xH,#0abH" % saddr)
            self.assertEqual(new_pc, 3)

    def test_b9_movw_sfrp_ax(self):
        for sfrp in range(0xff00, 0x10000, 2):
            sfrp_low = sfrp & 0xff
            mem = [0xb9, sfrp_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "MOVW 0%04xH,AX" % sfrp)
            self.assertEqual(new_pc, 2)

    def test_c8_cmp_saddr_imm8(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0xc8, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "CMP 0%04xH,#0abH" % saddr)
            self.assertEqual(new_pc, 3)

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

    def test_bd_bnz_rel(self):
        mem = [0xbd, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "BNZ $disp=ab")
        self.assertEqual(new_pc, 2)

    def test_be_mov_hl_plus_byte_a(self):
        mem = [0xBE, 0xAB]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "MOV [HL+0abH],A")
        self.assertEqual(new_pc, 2)

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

    def test_ca_addw_ax_imm16(self):
        for imm16 in (0x0000, 0xabcd, 0xffff):
            high = (imm16 >> 8) & 0xff
            low = imm16 & 0xff
            mem = [0xca, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "ADDW AX,#0%04xH" % imm16)
            self.assertEqual(new_pc, 3)

    def test_ce_xch_a_addr16(self):
        for addr16 in (0x0000, 0xabcd, 0xffff):
            low = addr16 & 0xff
            high = (addr16 >> 8) & 0xff
            mem = [0xce, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, 'XCH A,!0%04xH' % addr16)
            self.assertEqual(new_pc, 3)

    def test_d2_d4_d6_mov_regpair(self):
        d = {0xD2: "MOVW BC,AX", 0xD4: "MOVW DE,AX", 0xD6: "MOVW HL,AX"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_d8_and_saddr_imm8(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0xd8, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "AND 0%04xH,#0abH" % saddr)
            self.assertEqual(new_pc, 3)

    def test_da_subw_ax_imm16(self):
        for imm16 in (0x0000, 0xabcd, 0xffff):
            high = (imm16 >> 8) & 0xff
            low = imm16 & 0xff
            mem = [0xda, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "SUBW AX,#0%04xH" % imm16)
            self.assertEqual(new_pc, 3)

    def test_e2_e4_e6_xchw_ax_regpair(self):
        d = {0xE2: "XCHW AX,BC", 0xE4: "XCHW AX,DE", 0xE6: "XCHW AX,HL"}

        for opcode, expected_disasm in d.items():
            mem = [opcode]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, expected_disasm)
            self.assertEqual(new_pc, 1)

    def test_e8_or_saddr_imm8(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0xe8, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "OR 0%04xH,#0abH" % saddr)
            self.assertEqual(new_pc, 3)

    def test_ea_cmpw_ax_imm16(self):
        for imm16 in (0x0000, 0xabcd, 0xffff):
            high = (imm16 >> 8) & 0xff
            low = imm16 & 0xff
            mem = [0xea, low, high]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "CMPW AX,#0%04xH" % imm16)
            self.assertEqual(new_pc, 3)

    def test_f4_mov_a_sfr(self):
        for sfr in range(0xff00, 0x10000):
            sfr_low = sfr & 0xff
            mem = [0xf4, sfr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "MOV A,0%04xH" % sfr)
            self.assertEqual(new_pc, 2)

    def test_f6_mov_sfr_a(self):
        for sfr in range(0xff00, 0x10000):
            sfr_low = sfr & 0xff
            mem = [0xf6, sfr_low]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "MOV 0%04xH,A" % sfr)
            self.assertEqual(new_pc, 2)

    def test_f8_xor_saddr_imm8(self):
        for saddr in range(0xfe20, 0xff20):
            saddr_low = saddr & 0xff
            mem = [0xf8, saddr_low, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "XOR 0%04xH,#0abH" % saddr)
            self.assertEqual(new_pc, 3)

    def test_fe_movw_sfrp_imm16(self):
        for sfrp in range(0xff00, 0x10000, 2):
            sfrp_low = sfrp & 0xff
            mem = [0xfe, sfrp_low, 0xcd, 0xab]
            disasm, new_pc = disassemble(mem, pc=0)
            self.assertEqual(disasm, "MOVW 0%04xH,#0abcdH" % sfrp)
            self.assertEqual(new_pc, 4)

    def test_fa_br_rel(self):
        mem = [0xfa, 0xab]
        disasm, new_pc = disassemble(mem, pc=0)
        self.assertEqual(disasm, "BR $disp=ab")
        self.assertEqual(new_pc, 2)

def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
