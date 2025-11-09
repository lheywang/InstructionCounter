# Makefile
# author : l.heywang
# date : 09-11-2025
# brief : enable the usage of QEMU and python to precisely count the instructions.

# Settings
BUILD_FOLDER = build

# Output files
EXECUTABLE = $(BUILD_FOLDER)/executable.elf
LOGS = $(BUILD_FOLDER)/trace.log
DATA = $(BUILD_FOLDER)/data.json
REPORT_DIR = $(BUILD_FOLDER)/report


# Theses are copied from the makefile available on the contest.
# Any changes could reflect on large changes on the final count.
CC = riscv-none-elf-gcc
RISCV_CFLAGS :=-DPERFORMANCE_RUN=1 \
		-DITERATIONS=3 \
		-march=rv32im_zicsr \
		-mabi=ilp32 \
		-DPREALLOCATE=1 \
		-fvisibility=hidden \
		-DSTDIO_THRU_UART \
		-O3 \
		-mcmodel=medany \
		-fno-tree-loop-distribute-patterns\
		-funroll-all-loops \
		-falign-jumps=4 \
		-falign-functions=16 \
		-static \
		-Wall \
		-pedantic \
		-DFIXED_POINT

# Simulator
SIM = qemu-riscv32
SIM_FLAGS = -d in_asm,exec,nochain\
		   	-D $(LOGS)


# Note : We call the target makefile, to be always compliant with our needs.
$(EXECUTABLE): $(BUILD_FOLDER) 
	$(CC) $(RISCV_CFLAGS) -o $(EXECUTABLE) src/fft_int16_main.c src/kissfft_lib/kiss_fft.c -lm
# 	$(MAKE) ...

$(LOGS): $(EXECUTABLE)
	$(SIM) $(SIM_FLAGS) $(EXECUTABLE)

$(DATA): $(LOGS)
	./tool/parser.py $(LOGS) --output $(DATA)

count: $(DATA)
	./tool/report.py $(DATA) --output $(REPORT_DIR)

clean:
	rm -f $(LOGS)
	rm -f $(EXECUTABLE)
	rm -f $(DATA)
	rm -rf $(REPORT_DIR)

$(BUILD_FOLDER) : 
	mkdir -p $(BUILD_FOLDER)
