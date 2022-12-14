import os
import argparse
from control_functions import *

MemSize = 1000 # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.


class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name

        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        #read instruction memory
        #return 32 bit hex val
        return "".join([i for idx,i in enumerate(self.IMem) if (idx >= ReadAddress) and (idx < ReadAddress + 4)])


class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def readMem(self, ReadAddress):
        #read data memory
        #return 32 bit hex val
        return "".join([i for idx,i in enumerate(self.DMem) if (idx >= ReadAddress) and (idx < ReadAddress + 4)])

    def divideString(self, s, k, fill):
        l=[]
        if len(s) % k != 0:
            s += fill * (k - len(s) % k)
        for i in range(0, len(s), k):
            l.append(s[i:i + k])
        return l

    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
        curr_len = len(self.DMem)
        if int(Address,2) > curr_len:
            to_append = int(Address,2) - curr_len
            self.DMem += ["00000000"]*to_append
        curr_len = len(self.DMem)
        # WriteData is 32 to bit string
        bits_split = 8
        fill_remain = "0"
        array = self.divideString(WriteData, bits_split, fill_remain)

        array_counter = 0
        for i in range(int(Address,2),int(Address,2)+4):
            if i >= curr_len:
                self.DMem.append(array[array_counter])
            else:
                self.DMem[i] = array[array_counter]
            array_counter += 1

    def outputDataMem(self):
        curr_len = len(self.DMem)
        if 1000 > curr_len:
            to_append = 1000 - curr_len
            self.DMem += ["00000000"]*to_append
        resPath = self.ioDir + "/" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])


class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = ["00000000000000000000000000000000" for i in range(32)]

    def readRF(self, Reg_addr):
        # Fill in
        return self.Registers[int(Reg_addr,2)]

    def writeRF(self, Reg_addr, Wrt_reg_data):
        # Fill in
        # print(Reg_addr,Wrt_reg_data,self.Registers[int(Reg_addr,2)])
        if int(Reg_addr, 2):
            self.Registers[int(Reg_addr,2)] = Wrt_reg_data

    def outputRF(self, cycle):
        op = ["State of RF after executing cycle:\t" + str(cycle) + "\n"]
        op.extend([str(val) + "\n" for val in self.Registers])
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0, "branch":0, "jump":0}
        self.ID = {"nop": False, "Instr": 0, "PC": 0, "branch":0, "jump":0}
        self.EX = {"nop": False, "Operand1": 0, "Operand1": 0, "Imm": 0,
                   "mux_out1": 0, "mux_out2": 0, "DestReg": 0,
                   "is_I_type": False, "RdDMem": 0, "WrDMem": 0,
                   "AluOperation": 0, "WBEnable": 0, "PC": 0, "branch":0,
                   "AluControlInput": 0, "jump":0}
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0,
                   "Rt": 0, "DestReg": 0, "RdDMem": 0, "WrDMem": 0,
                   "WBEnable": 0, "PC": 0, "branch":0, "jump":0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "DestReg": 0,
                   "WBEnable": 0, "PC": 0, "branch":0, "jump":0}


class Core(object):

    def __init__(self, ioDir, baseioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem
        self.baseioDir = baseioDir

    def calculatePerformance(self, write_option, core_text):
        self.opFilePath = self.baseioDir + "/PerformanceMetrics_Result.txt"
        instruction_count = len(self.ext_imem.IMem) / 4
        with open(self.opFilePath, write_option) as f:
            f.write(f'\n{core_text} Core Performance Metrics-----------------------------\n')
            f.write(f'Number of cycles taken: {self.cycle}\n')
            f.write(f'Cycles per instruction: {self.cycle / instruction_count}\n')
            f.write(f'Instructions per cycle: {instruction_count / self.cycle}\n')


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "/SS_", ioDir, imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"

    def calculatePerformance(self, write_option):
        super().calculatePerformance(write_option, 'Single Stage')

    def step(self):
        # Your implementation
        if self.state.IF["nop"]:
            self.halted = True
        # ----------------------------- IF stage -------------------------------

        instruction_fetch(self.state, self.nextState, self.ext_imem)
        self.nextState.IF["PC"] = self.state.IF["PC"]
        # This logic is for single Stage
        self.state = self.nextState

        # ----------------------------- ID stage -------------------------------

        instruction_decode(self.state, self.nextState, self.myRF, self.ext_dmem)
        # This logic is for single Stage
        self.state = self.nextState

        # ----------------------------- EX stage -------------------------------

        instruction_exec(self.state, self.nextState, self.myRF, self.ext_dmem)
        # This logic is for single Stage
        self.state = self.nextState

        # ----------------------------- MEM stage ------------------------------

        instruction_mem(self.state, self.nextState, self.myRF, self.ext_dmem)

        # This logic is for single Stage
        self.state = self.nextState

        # ----------------------------- WB stage -------------------------------

        write_back(self.state, self.nextState, self.myRF)

        # This logic is for single Stage
        self.state = State()
        self.state.IF["PC"] = self.nextState.IF["PC"]
        self.state.IF["nop"] = self.nextState.IF["nop"]

        # self.halted = True


        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ...

        # self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.nextState = State()
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["State after executing cycle:\t" + str(cycle) + "\n"]
        printstate.append("IF.PC:\t" + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop:\t" + str(int(state.IF["nop"])) + "\n")

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "/FS_", ioDir, imem, dmem)
        self.opFilePath = ioDir + "/StateResult_FS.txt"

    def calculatePerformance(self, write_option):
        super().calculatePerformance(write_option, 'Five Stage')

    def step(self):
        # Your implementation
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True
            # return
        # --------------------- WB stage ---------------------

        write_back(self.state, self.nextState, self.myRF)

        # --------------------- MEM stage --------------------

        instruction_mem(self.state, self.nextState, self.myRF, self.ext_dmem)

        # --------------------- EX stage ---------------------

        instruction_exec(self.state, self.nextState, self.myRF, self.ext_dmem)

        # --------------------- ID stage ---------------------


        instruction_decode(self.state, self.nextState, self.myRF, self.ext_dmem)

        # --------------------- IF stage ---------------------

        instruction_fetch(self.state, self.nextState, self.ext_imem)

        if (self.cycle == 0 and self.state.IF["nop"] == False) or self.state.IF["jump"]:
            self.nextState.IF["PC"] = self.state.IF["PC"] + 4

        # self.halted = True


        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.nextState = State()
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


if __name__ == "__main__":

    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = args.iodir or os.path.dirname(__file__)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)

    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        if not ssCore.halted:
            ssCore.step()
        # if ssCore.halted :
        #     break
        if not fsCore.halted:
            fsCore.step()
        # if fsCore.halted :
        #     break
        if ssCore.halted and fsCore.halted:
            break

    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()

    # dump performance metric
    ssCore.calculatePerformance('w')
    fsCore.calculatePerformance('a')
