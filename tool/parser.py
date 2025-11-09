#!/bin/env python3
# ========================================================================================
# file : parser.py
# author : l.heywang
# date : 09/11/2025
# 
# brief : Parse a QEMU log file (some parameters MUST be passed, use the Makefile)
# ========================================================================================

import json
import argparse
from pathlib import Path

def parse_trace(input : str) -> tuple[int, str]:
    """
        Parse a trace line into differents sub-blocks : 

            Trace 0: 0x7f25d0600980 [00000000/00000000000156c6/0101c078/00000200] memset

        Returns the address of the called function, and it's name (if available).
    """

    tmp = input.split()

    # Basid checks : 
    if not tmp[0] == "Trace" : 
        print("No trace log found !")
        return (-1, "error")
    if not tmp[1] == "0:" : 
        print("Wrong hart ID !")
        return (-2, "wrong hart")
    
    # We only want the third arguments, and remove some elements
    qemu_data = tmp[3][1:-1].split("/")

    # Compute the call name
    name = tmp[4] if len(tmp) > 4 else ""

    # Return the usefull data
    return (int(qemu_data[1], 16), name)


def parse_instruction(input: str) -> tuple[int, int, str, list[str]]:
    """
        Parse an instruction line, and return the address, opcode, mnemonics and args.

            0x000156b8:  c30c              sw                      a1,0(a4)
    """
    tmp = input.split(" ")
    tmp = [x for x in tmp if x] # Filter empty elements

    #"" Identify args
    args =  tmp[3].split(",") if len(tmp) > 3 else []

    # Returns
    return (int(tmp[0][:-1], 16), int(tmp[1], 16), tmp[2], args)

def parse_file(source: Path) -> dict:
    """
        Perform the parsing of the file !
        Iterate over each line of the passed file, and return a final dict, to be
        exported as JSON for report generation !
    """
    # Initialize the output dict
    output = dict()
    output["blocks"] = dict()
    output["calls"] = dict()

    # Create a temporary block storage
    block = dict()
    addr = 0

    with open(str(source), "r") as file:
        
        # Iterating over each lines :
        for line in file.readlines()[1:]: # Ignore the first line, simplify the logic !

            # CThe first logic handle the block parsing, and new blocks
            if line.startswith("--"):  # This mean : new block, so, commit the previous one !
                output["blocks"][f"{addr}"] = block

            elif line.startswith("IN:"):    # Clean the temp block (we already commited it)
                block = dict()
                addr = None

            elif line.startswith("0x"):
                called, op, name, args = parse_instruction(line)

                 # Set addr to FIRST instruction in block
                if addr is None:  # ← Check if it's the first instruction
                    addr = called

                if name not in block.keys():
                    block[name] = 1
                else:
                    block[name] += 1

            # The last logic count each calls !
            elif line.startswith("Trace 0:"):
                called, name = parse_trace(line)

                if f"{called}" not in output["calls"].keys():
                    output["calls"][f"{called}"] = dict()
                    output["calls"][f"{called}"]["name"] = name
                    output["calls"][f"{called}"]["count"] = 1
                else:
                    output["calls"][f"{called}"]["count"] += 1 

        # Ensure the last block is always added !
        output["blocks"][f"{addr}"] = block

    return output

def json_output(target: Path, data: dict) -> None:
    """
        Output the correctly formatted JSON data
    """

    with open(str(target), "w+") as file:
        json.dump(data, file, indent=4)

    return


if __name__ == "__main__" : 
    # Argparse config
    parser = argparse.ArgumentParser(
        description="Parse a QEMU log file to a computer oriented JSON file"
    )
    parser.add_argument("input", help="Input .log file")
    parser.add_argument("-o", "--output", default="data.json", help="Output .json file")
    args = parser.parse_args()

    # Path generation : 
    input = Path(args.input)
    output = Path(args.output)

    # Start the file parsing
    data = parse_file(input)

    # Create output file : 
    json_output(output, data)

    


