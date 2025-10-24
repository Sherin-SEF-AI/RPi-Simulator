"""
Raspberry Pi OS Emulation Layer

Provides virtual file system, process management, and system calls
to simulate the Raspberry Pi OS environment.
"""

import os
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import time


class VirtualFileSystem:
    """Virtual file system overlay for Pi OS simulation"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.overlay_path = base_path / ".pistudio_overlay"
        self.overlay_path.mkdir(exist_ok=True)
        
        # Standard Pi directories
        self.pi_dirs = {
            "/home/pi": self.overlay_path / "home" / "pi",
            "/boot": self.overlay_path / "boot",
            "/etc": self.overlay_path / "etc",
            "/var/log": self.overlay_path / "var" / "log",
            "/tmp": self.overlay_path / "tmp",
            "/dev": self.overlay_path / "dev"
        }
        
        self._create_pi_structure()
        
    def _create_pi_structure(self):
        """Create standard Raspberry Pi directory structure"""
        for virt_path, real_path in self.pi_dirs.items():
            real_path.mkdir(parents=True, exist_ok=True)
            
        # Create standard Pi files
        self._create_pi_files()
        
    def _create_pi_files(self):
        """Create standard Raspberry Pi system files"""
        # /boot/config.txt
        config_txt = self.pi_dirs["/boot"] / "config.txt"
        with open(config_txt, "w") as f:
            f.write("""# PiStudio Virtual Pi Configuration
# Enable I2C
dtparam=i2c_arm=on
dtparam=i2c1=on

# Enable SPI
dtparam=spi=on

# Enable UART
enable_uart=1

# GPIO configuration
gpio=2,3=a0  # I2C
gpio=9,10,11=a0  # SPI
gpio=14,15=a0  # UART

# PWM
dtoverlay=pwm,pin=18,func=2
dtoverlay=pwm,pin=19,func=2
""")

        # /etc/os-release
        os_release = self.pi_dirs["/etc"] / "os-release"
        with open(os_release, "w") as f:
            f.write("""PRETTY_NAME="PiStudio Virtual Raspberry Pi OS"
NAME="Raspberry Pi OS"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
""")

        # /proc/cpuinfo simulation
        proc_dir = self.overlay_path / "proc"
        proc_dir.mkdir(exist_ok=True)
        
        cpuinfo = proc_dir / "cpuinfo"
        with open(cpuinfo, "w") as f:
            f.write("""processor	: 0
model name	: ARMv7 Processor rev 3 (v7l)
BogoMIPS	: 108.00
Features	: half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm crc32 
CPU implementer	: 0x41
CPU architecture: 7
CPU variant	: 0x0
CPU part	: 0xd08
CPU revision	: 3

Hardware	: BCM2711
Revision	: c03111
Serial		: 10000000deadbeef
Model		: Raspberry Pi 4 Model B Rev 1.1
""")

        # Device tree simulation
        self._create_device_tree()
        
    def _create_device_tree(self):
        """Create device tree simulation files"""
        dev_dir = self.pi_dirs["/dev"]
        
        # GPIO devices
        (dev_dir / "gpiochip0").touch()
        (dev_dir / "gpiomem").touch()
        
        # I2C devices
        for i in range(2):
            (dev_dir / f"i2c-{i}").touch()
            
        # SPI devices
        for i in range(2):
            (dev_dir / f"spidev0.{i}").touch()
            
        # UART devices
        (dev_dir / "ttyAMA0").touch()
        (dev_dir / "serial0").touch()
        
    def get_virtual_path(self, path: str) -> Path:
        """Convert virtual path to real overlay path"""
        for virt_path, real_path in self.pi_dirs.items():
            if path.startswith(virt_path):
                rel_path = path[len(virt_path):].lstrip("/")
                return real_path / rel_path
                
        # Default to overlay root
        return self.overlay_path / path.lstrip("/")
        
    def read_file(self, path: str) -> Optional[str]:
        """Read file from virtual filesystem"""
        real_path = self.get_virtual_path(path)
        try:
            return real_path.read_text()
        except FileNotFoundError:
            return None
            
    def write_file(self, path: str, content: str) -> bool:
        """Write file to virtual filesystem"""
        real_path = self.get_virtual_path(path)
        try:
            real_path.parent.mkdir(parents=True, exist_ok=True)
            real_path.write_text(content)
            return True
        except Exception:
            return False


class ProcessManager:
    """Virtual process management for Pi OS simulation"""
    
    def __init__(self):
        self.processes: Dict[int, Dict[str, Any]] = {}
        self.next_pid = 1000
        self.system_processes = self._create_system_processes()
        
    def _create_system_processes(self) -> Dict[int, Dict[str, Any]]:
        """Create standard system processes"""
        return {
            1: {"name": "systemd", "cmd": "/sbin/init", "state": "S", "cpu": 0.1},
            2: {"name": "kthreadd", "cmd": "[kthreadd]", "state": "S", "cpu": 0.0},
            100: {"name": "systemd-logind", "cmd": "/lib/systemd/systemd-logind", "state": "S", "cpu": 0.0},
            200: {"name": "dbus-daemon", "cmd": "/usr/bin/dbus-daemon", "state": "S", "cpu": 0.0},
            300: {"name": "ssh", "cmd": "/usr/sbin/sshd", "state": "S", "cpu": 0.0},
            400: {"name": "dhcpcd", "cmd": "/sbin/dhcpcd", "state": "S", "cpu": 0.0},
        }
        
    def start_process(self, command: str, args: List[str] = None) -> int:
        """Start a new virtual process"""
        pid = self.next_pid
        self.next_pid += 1
        
        self.processes[pid] = {
            "name": Path(command).name,
            "cmd": f"{command} {' '.join(args or [])}",
            "state": "R",  # Running
            "cpu": 0.0,
            "memory": 1024,  # KB
            "start_time": time.time()
        }
        
        return pid
        
    def kill_process(self, pid: int) -> bool:
        """Kill a virtual process"""
        if pid in self.processes:
            del self.processes[pid]
            return True
        return False
        
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of all processes"""
        all_processes = []
        
        # Add system processes
        for pid, proc in self.system_processes.items():
            all_processes.append({"pid": pid, **proc})
            
        # Add user processes
        for pid, proc in self.processes.items():
            all_processes.append({"pid": pid, **proc})
            
        return all_processes
        
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get information about a specific process"""
        if pid in self.system_processes:
            return {"pid": pid, **self.system_processes[pid]}
        elif pid in self.processes:
            return {"pid": pid, **self.processes[pid]}
        return None


class SystemCallEmulator:
    """Emulate common system calls and commands"""
    
    def __init__(self, vfs: VirtualFileSystem, proc_mgr: ProcessManager):
        self.vfs = vfs
        self.proc_mgr = proc_mgr
        
        # Command implementations
        self.commands = {
            "ps": self._cmd_ps,
            "ls": self._cmd_ls,
            "cat": self._cmd_cat,
            "echo": self._cmd_echo,
            "pwd": self._cmd_pwd,
            "whoami": self._cmd_whoami,
            "uname": self._cmd_uname,
            "lscpu": self._cmd_lscpu,
            "free": self._cmd_free,
            "df": self._cmd_df,
            "lsusb": self._cmd_lsusb,
            "lsmod": self._cmd_lsmod,
            "gpio": self._cmd_gpio,
            "i2cdetect": self._cmd_i2cdetect,
            "raspi-config": self._cmd_raspi_config,
        }
        
    def execute_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """Execute a system command"""
        args = args or []
        
        if command in self.commands:
            try:
                result = self.commands[command](args)
                return {
                    "success": True,
                    "output": result,
                    "exit_code": 0
                }
            except Exception as e:
                return {
                    "success": False,
                    "output": f"{command}: {str(e)}",
                    "exit_code": 1
                }
        else:
            return {
                "success": False,
                "output": f"{command}: command not found",
                "exit_code": 127
            }
            
    def _cmd_ps(self, args: List[str]) -> str:
        """Simulate ps command"""
        processes = self.proc_mgr.get_process_list()
        
        output = ["  PID TTY          TIME CMD"]
        for proc in processes[:10]:  # Limit output
            output.append(f"{proc['pid']:5d} pts/0    00:00:00 {proc['name']}")
            
        return "\n".join(output)
        
    def _cmd_ls(self, args: List[str]) -> str:
        """Simulate ls command"""
        path = args[0] if args else "/home/pi"
        
        # Simulate common Pi directories
        if path == "/home/pi":
            return "Desktop  Documents  Downloads  Pictures  Videos  projects"
        elif path == "/":
            return "bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var"
        elif path == "/boot":
            return "config.txt  cmdline.txt  kernel.img  start.elf"
        else:
            return f"ls: cannot access '{path}': No such file or directory"
            
    def _cmd_cat(self, args: List[str]) -> str:
        """Simulate cat command"""
        if not args:
            return "cat: missing file operand"
            
        content = self.vfs.read_file(args[0])
        return content if content else f"cat: {args[0]}: No such file or directory"
        
    def _cmd_echo(self, args: List[str]) -> str:
        """Simulate echo command"""
        return " ".join(args)
        
    def _cmd_pwd(self, args: List[str]) -> str:
        """Simulate pwd command"""
        return "/home/pi"
        
    def _cmd_whoami(self, args: List[str]) -> str:
        """Simulate whoami command"""
        return "pi"
        
    def _cmd_uname(self, args: List[str]) -> str:
        """Simulate uname command"""
        if "-a" in args:
            return "Linux raspberrypi 5.10.63-v7l+ #1459 SMP Wed Oct 6 16:41:57 BST 2021 armv7l GNU/Linux"
        return "Linux"
        
    def _cmd_lscpu(self, args: List[str]) -> str:
        """Simulate lscpu command"""
        return """Architecture:        armv7l
Byte Order:          Little Endian
CPU(s):              4
On-line CPU(s) list: 0-3
Thread(s) per core:  1
Core(s) per socket:  4
Socket(s):           1
Vendor ID:           ARM
Model:               3
Model name:          Cortex-A72
Stepping:            r0p3
CPU max MHz:         1500.0000
CPU min MHz:         600.0000"""

    def _cmd_free(self, args: List[str]) -> str:
        """Simulate free command"""
        return """              total        used        free      shared  buff/cache   available
Mem:        4194304      512000     3200000       32768      482304     3500000
Swap:        102400           0      102400"""

    def _cmd_df(self, args: List[str]) -> str:
        """Simulate df command"""
        return """Filesystem     1K-blocks    Used Available Use% Mounted on
/dev/root       15718400 4500000  10800000  30% /
devtmpfs         1847424       0   1847424   0% /dev
tmpfs            2097152       0   2097152   0% /dev/shm
tmpfs             838860    8460    830400   2% /run
tmpfs               5120       4      5116   1% /run/lock
/dev/mmcblk0p1    258095   54395    203701  22% /boot"""

    def _cmd_lsusb(self, args: List[str]) -> str:
        """Simulate lsusb command"""
        return """Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 002: ID 2109:3431 VIA Labs, Inc. Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub"""

    def _cmd_lsmod(self, args: List[str]) -> str:
        """Simulate lsmod command"""
        return """Module                  Size  Used by
i2c_bcm2835            16384  0
spi_bcm2835            20480  0
gpio_bcm2835           16384  0
pwm_bcm2835            16384  0"""

    def _cmd_gpio(self, args: List[str]) -> str:
        """Simulate gpio command (wiringPi)"""
        if "readall" in args:
            return """ +-----+-----+---------+------+---+---Pi 4---+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
 |   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5v      |     |     |
 |   3 |   9 |   SCL.1 |   IN | 1 |  5 || 6  |   |      | 0v      |     |     |
 |   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 1 | IN   | TxD     | 15  | 14  |
 |     |     |      0v |      |   |  9 || 10 | 1 | IN   | RxD     | 16  | 15  |
 |  17 |   0 | GPIO. 0 |   IN | 0 | 11 || 12 | 0 | IN   | GPIO. 1 | 1   | 18  |
 |  27 |   2 | GPIO. 2 |   IN | 0 | 13 || 14 |   |      | 0v      |     |     |
 |  22 |   3 | GPIO. 3 |   IN | 0 | 15 || 16 | 0 | IN   | GPIO. 4 | 4   | 23  |
 |     |     |    3.3v |      |   | 17 || 18 | 0 | IN   | GPIO. 5 | 5   | 24  |
 |  10 |  12 |    MOSI |   IN | 0 | 19 || 20 |   |      | 0v      |     |     |
 |   9 |  13 |    MISO |   IN | 0 | 21 || 22 | 0 | IN   | GPIO. 6 | 6   | 25  |
 |  11 |  14 |    SCLK |   IN | 0 | 23 || 24 | 1 | IN   | CE0     | 10  | 8   |
 |     |     |      0v |      |   | 25 || 26 | 1 | IN   | CE1     | 11  | 7   |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+"""
        return "gpio: command not implemented"
        
    def _cmd_i2cdetect(self, args: List[str]) -> str:
        """Simulate i2cdetect command"""
        if "-y" in args and "1" in args:
            return """     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- 27 -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- 76 --"""
        return "i2cdetect: command requires -y flag and bus number"
        
    def _cmd_raspi_config(self, args: List[str]) -> str:
        """Simulate raspi-config command"""
        return """Raspberry Pi Software Configuration Tool (raspi-config)
This tool provides a straightforward way of doing initial configuration of the Raspberry Pi.
Run with sudo raspi-config for full functionality."""


class PiOSEmulator:
    """Complete Raspberry Pi OS emulation layer"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.vfs = VirtualFileSystem(project_path)
        self.proc_mgr = ProcessManager()
        self.syscall_emu = SystemCallEmulator(self.vfs, self.proc_mgr)
        
        # System state
        self.boot_time = time.time()
        self.uptime = 0.0
        
    def execute_shell_command(self, command: str) -> Dict[str, Any]:
        """Execute a shell command in the emulated environment"""
        parts = command.strip().split()
        if not parts:
            return {"success": True, "output": "", "exit_code": 0}
            
        cmd = parts[0]
        args = parts[1:]
        
        return self.syscall_emu.execute_command(cmd, args)
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        self.uptime = time.time() - self.boot_time
        
        return {
            "hostname": "raspberrypi",
            "kernel": "5.10.63-v7l+",
            "architecture": "armv7l",
            "uptime": self.uptime,
            "load_average": [0.1, 0.05, 0.02],
            "memory": {
                "total": 4194304,  # 4GB in KB
                "used": 512000,
                "free": 3200000,
                "available": 3500000
            },
            "cpu": {
                "model": "ARM Cortex-A72",
                "cores": 4,
                "frequency": 1500,  # MHz
                "temperature": 45.2  # °C
            },
            "storage": {
                "total": 15718400,  # KB
                "used": 4500000,
                "available": 10800000
            }
        }
        
    def get_gpio_state(self) -> Dict[int, Dict[str, Any]]:
        """Get current GPIO pin states"""
        # This would integrate with the GPIO controller
        gpio_state = {}
        
        for pin in range(28):  # GPIO 0-27
            gpio_state[pin] = {
                "mode": "IN",
                "value": 0,
                "pull": "OFF",
                "function": "GPIO"
            }
            
        return gpio_state
        
    def enable_interface(self, interface: str) -> bool:
        """Enable hardware interface (I2C, SPI, UART, etc.)"""
        config_path = "/boot/config.txt"
        config_content = self.vfs.read_file(config_path) or ""
        
        interface_configs = {
            "i2c": "dtparam=i2c_arm=on",
            "spi": "dtparam=spi=on", 
            "uart": "enable_uart=1",
            "camera": "start_x=1",
            "ssh": "# SSH enabled via raspi-config"
        }
        
        if interface in interface_configs:
            config_line = interface_configs[interface]
            if config_line not in config_content:
                config_content += f"\n{config_line}\n"
                return self.vfs.write_file(config_path, config_content)
                
        return False
        
    def install_package(self, package_name: str) -> Dict[str, Any]:
        """Simulate package installation"""
        # Simulate apt install
        common_packages = {
            "python3-pip": "Python package installer",
            "git": "Version control system",
            "vim": "Text editor",
            "htop": "Process viewer",
            "i2c-tools": "I2C utilities",
            "python3-rpi.gpio": "Python GPIO library",
            "python3-gpiozero": "Simple GPIO library"
        }
        
        if package_name in common_packages:
            return {
                "success": True,
                "output": f"Reading package lists...\nBuilding dependency tree...\nInstalling {package_name}...\n{package_name} installed successfully.",
                "description": common_packages[package_name]
            }
        else:
            return {
                "success": False,
                "output": f"E: Unable to locate package {package_name}",
                "description": None
            }