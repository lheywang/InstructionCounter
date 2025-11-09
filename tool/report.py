#!/bin/env python3
# ========================================================================================
# file : report.py
# author : l.heywang
# date : 09/11/2025
#
# brief :   Parse a JSON output file (generated from parser.py) to create a nice report
#           (markdown formatted) and output some stats !
# ========================================================================================

import json
import argparse
import datetime
from pathlib import Path


def write_summary(data: dict, target: Path) -> None:
    """
    Write a summary, with all infos but no details
    """
    summary = target / Path("summary.md")
    with open(summary, "w+") as f:
        f.write("# **Code analysis report**\n\n")

        f.write("## Counts\n\n")
        f.write(f"Total instructions : {data["instructions"]:,}<br>\n")
        f.write(f"Total cycles (approx) : {data["cycles"]:,}<br>\n")
        f.write("*More on theses files [instructions cycles](instrcycles.md)*<br>\n")

        f.write("## CPI\n\n")
        f.write(f"Global CPI : {data["cpi"]:.3f} <br>\n")
        f.write(f"Global IPC : {data["ipc"]:.3f} <br>\n")
        f.write("*More on this file [ipc/cpi](cpi.md)*<br>\n")

        f.write("## Densities\n\n")
        f.write(f"Total jumps proportion : {data["densities"]["percents"]["jumps"]:.3f} %<br>\n")
        f.write(f"Total conditions proportion : {data["densities"]["percents"]["conditions"]:.3f} %<br>\n")
        f.write(f"Total arithmetic proportion : {data["densities"]["percents"]["arithmetic"]:.3f} %<br>\n")
        f.write(f"Total muldiv proportion : {data["densities"]["percents"]["muldiv"]:.3f} %<br>\n")
        f.write(f"Total memory proportion : {data["densities"]["percents"]["memory"]:.3f} %<br>\n")
        f.write(f"Total special proportion : {data["densities"]["percents"]["special"]:.3f} %<br>\n")
        f.write("*More on this file [densities](densities.md)*<br>\n")

        f.write("## Functions\n\n")
        f.write(f"Total functions number : {data["averages"]["func_number"]} <br>\n")
        f.write(f"Median instructions per functions : {data["averages"]["instr_per_func"]:.3f} <br>\n")
        f.write("*More on this file [functions](functions.md)*<br>\n")

    return


def write_functions(data: dict, target: Path) -> None:
    """
    Write a functions summary, with all details
    """

    file = target / Path("functions.md")
    with open(file, "w+") as f:
        f.write("# **Functions detailled report**\n\n")

        for func, opcodes in data["func_used_instr"].items():
            f.write(f"## {func}\n\n")

            f.write("| Opcode | Count |\n")
            f.write("| ------------- | ------------------ |\n")

            print(data["func_used_instr"][func])
            for opcode, count in opcodes.items():
                f.write(f"| {opcode} | {count} |\n")

        f.write("---\n")
        f.write("*Return to [summary](summary.md)*<br>\n")

    return


def write_densities(data: dict, target: Path) -> None:
    """
    Write a densities summary, with all details
    """

    file = target / Path("densities.md")
    with open(file, "w+") as f:
        f.write("# **Densities detailled report**\n\n")

        for func, tmp in data["func_densities"].items():
            f.write(f"## {func}\n\n")

            f.write("| Instruction type | Proportion |\n")
            f.write("| ---------------- | ---------- |\n")

            for type, percents in tmp["percents"].items():
                f.write(f"| {type} | {percents:.3f} |\n")
                
        f.write("---\n")
        f.write("*Return to [summary](summary.md)*<br>\n")

    return


def write_cycles_instructions(data: dict, target: Path) -> None:
    """
    Write a cycles summary, with all details
    """

    file = target / Path("instrcycles.md")
    with open(file, "w+") as f:
        f.write("# **Instructions and cycles detailled report**\n\n")

        f.write("## Functions details\n\n")
        f.write("| Function name | Instructions count | Cycles counts |\n")
        f.write("| ------------- | ------------------ | ------------- |\n")

        for func, instr in data["func_calls_instr"].items():
            f.write(f"| {func} | {instr} | {data["func_calls_cycles"][func]} |\n")

        f.write("\n*Table is ordered by descending instructions counts*")

        f.write("---\n")
        f.write("*Return to [summary](summary.md)*<br>\n")

    return


def write_CPI(data: dict, target: Path) -> None:
    """
    Write a CPI summary, with all details
    """

    file = target / Path("cpi.md")
    with open(file, "w+") as f:
        f.write("# **CPI detailled report**\n\n")

        f.write("## Global\n\n")
        f.write(f"Global CPI : {data["cpi"]:.3f} <br>\n")
        f.write(f"Global IPC : {data["ipc"]:.3f} <br>\n")

        f.write("## Functions details\n\n")
        f.write("| Function name | CPI | IPC |\n")
        f.write("| ------------- | --- | --- |\n")

        for func, cpi in data["func_cpi"].items():
            f.write(f"| {func} | {cpi:3f} | {(1/cpi):3f} |\n")

        f.write("---\n")
        f.write("*Return to [summary](summary.md)*<br>\n")

    return


def read_json(source: Path) -> dict:
    """
    Read the JSON file, and produce a python accessible dict
    """

    ret = dict()
    with open(str(source), "r") as file:
        ret = json.load(file)

    return ret


if __name__ == "__main__":
    # Argparse config
    parser = argparse.ArgumentParser(
        description="Parse a compute JSON file to a computer oriented JSON file"
    )
    parser.add_argument("input", help="Input .json file")
    parser.add_argument(
        "-o", "--output", default="report/", help="Output target folder"
    )
    args = parser.parse_args()

    # Path generation :
    input = Path(args.input)
    output = Path(args.output)

    # Prepare output folder
    output.mkdir(parents=True, exist_ok=True)

    # Read the base data
    data = read_json(input)

    # Write different pieces
    write_summary(data, output)
    write_functions(data, output)
    write_densities(data, output)
    write_cycles_instructions(data, output)
    write_CPI(data, output)
