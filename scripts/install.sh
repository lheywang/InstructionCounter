#!/usr/bin/env bash
set -e  # Exit on error

# Choose install dir (change if needed)
INSTALL_DIR="/opt/riscv"

# Create directory if not exists
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

wget https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases/download/v13.2.0-1/xpack-riscv-none-elf-gcc-13.2.0-1-linux-x64.tar.gz
wget https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases/download/v13.2.0-1/xpack-riscv-none-elf-gcc-13.2.0-1-linux-x64.tar.gz.sha

sha256sum -c xpack-riscv-none-elf-gcc-13.2.0-1-linux-x64.tar.gz.sha

tar -xf xpack-riscv-none-elf-gcc-13.2.0-1-linux-x64.tar.gz

# The folder will be something like:
# xpack-riscv-none-elf-gcc-13.2.0-1
TOOLCHAIN_DIR=$(find . -maxdepth 1 -type d -name "xpack-riscv-none-elf-gcc-*" | head -n 1)

# Add to PATH (temporary)
export PATH="$INSTALL_DIR/$TOOLCHAIN_DIR/bin:$PATH"

rm xpack-riscv-none-elf-gcc-13.2.0-1-linux-x64.tar.gz
rm xpack-riscv-none-elf-gcc-13.2.0-1-linux-x64.tar.gz.sha 

echo "Toolchain installed to $INSTALL_DIR/$TOOLCHAIN_DIR/bin"
echo "To make it permanent, add this line to your ~/.bashrc:"
echo "export PATH=\"$INSTALL_DIR/$TOOLCHAIN_DIR/bin:\$PATH\""

echo "Install qemu-user with your package manager to be able to simulate"
echo "    sudo dnf install qemu-user"
echo "    sudo apt-get install qemu-user"