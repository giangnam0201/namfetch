#!/usr/bin/env python3
"""namfetch - a neofetch-like tool that runs on every device Python runs on.

Native: Windows, macOS, Linux (with per-distro logos), ChromeOS, *BSD, Solaris,
        Haiku, Cygwin, MSYS2.
Mobile: Android (Termux), iOS (a-Shell / Pythonista).

Stdlib only. Optional external commands (nmcli, iwgetid, pmset, airport,
xrandr, lspci, ...) are used when present to enrich output.
"""
from __future__ import annotations

import ctypes
import getpass
import json
import locale
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import timedelta


# --------------------------------------------------------------------------- #
# Colors                                                                      #
# --------------------------------------------------------------------------- #
class C:
    R = "\033[0m"
    B = "\033[1m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


def enable_ansi_on_windows() -> None:
    if os.name != "nt":
        return
    try:
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if k.GetConsoleMode(h, ctypes.byref(mode)):
            k.SetConsoleMode(h, mode.value | 0x0004)
    except Exception:
        pass


def _run(cmd: list[str], timeout: float = 2.0) -> str:
    try:
        out = subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, timeout=timeout
        )
        return out.decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


# --------------------------------------------------------------------------- #
# OS / distro detection                                                       #
# --------------------------------------------------------------------------- #
def _read_os_release() -> dict:
    try:
        with open("/etc/os-release") as f:
            kv = {}
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                kv[k] = v.strip().strip('"')
            return kv
    except Exception:
        return {}


def detect_os() -> str:
    s = platform.system()
    if s == "Linux":
        if "ANDROID_ROOT" in os.environ or "ANDROID_DATA" in os.environ:
            return "android"
        if os.path.exists("/system/build.prop"):
            return "android"
        if "microsoft" in platform.release().lower() or "WSL_DISTRO_NAME" in os.environ:
            return "wsl"
        rel = _read_os_release()
        idl = (rel.get("ID") or "").lower()
        like = (rel.get("ID_LIKE") or "").lower()
        if idl == "chromeos" or os.path.exists("/etc/lsb-release") and "CHROMEOS" in open("/etc/lsb-release").read():
            return "chromeos"
        for token in (idl, like):
            for distro in ("arch", "ubuntu", "debian", "fedora", "alpine",
                           "raspbian", "linuxmint", "manjaro", "centos",
                           "rhel", "nixos", "gentoo", "opensuse"):
                if distro in token:
                    return distro
        return "linux"
    if s == "Darwin":
        m = platform.machine().lower()
        if m.startswith(("iphone", "ipad", "ipod")):
            return "ios"
        if "PYTHONISTA_DOC" in os.environ or os.path.expanduser("~").startswith("/var/mobile"):
            return "ios"
        return "macos"
    if s == "Windows":
        return "windows"
    if s.endswith("BSD"):
        return "bsd"
    if s == "Haiku":
        return "haiku"
    if s == "SunOS":
        return "solaris"
    if s.startswith(("CYGWIN", "MSYS", "MINGW")):
        return "cygwin"
    return "unknown"


# --------------------------------------------------------------------------- #
# ASCII logos                                                                 #
# --------------------------------------------------------------------------- #
LOGOS = {
    "windows": (C.CYAN, [
        "        ,.=:!!t3Z3z.,           ",
        "       :tt:::tt333EE3           ",
        "       Et:::ztt33EEEL  @Ee.,    ",
        "      ;tt:::tt333EE7  ;EEEEEEttt",
        "     :Et:::zt333EEQ.  $EEEEEttt:",
        "     it::::tt333EEF  @EEEEEEttt:",
        "    ;3=*^```\"*4EEV   :EEEEEEttt:",
        "    ,.=::::it=., `   @EEEEEEtt::",
        "   ;::::::::zt33)    \"4EEEtttji3",
        "  :t::::::::tt33.:Z3z..  `` ,..g",
        "  i::::::::zt33F  AEEEtttt::::st",
        " ;:::::::::t33V   ;EEEttttt::::t",
        " E::::::::zt33L   @EEEtttt::::z3",
        "{3=*^```\"*4E3)    ;EEEtttt:::::t",
        "                   ` :EEEEtttt::",
    ]),
    "macos": (C.GREEN, [
        "                    'c.          ",
        "                 ,xNMM.          ",
        "               .OMMMMo           ",
        "               OMMM0,            ",
        "     .;loddo:' loolloddol;.      ",
        "   cKMMMMMMMMMMNWMMMMMMMMMM0:    ",
        " .KMMMMMMMMMMMMMMMMMMMMMMMWd.    ",
        " XMMMMMMMMMMMMMMMMMMMMMMMX.      ",
        ";MMMMMMMMMMMMMMMMMMMMMMMM:       ",
        ":MMMMMMMMMMMMMMMMMMMMMMMM:       ",
        ".MMMMMMMMMMMMMMMMMMMMMMMMX.      ",
        " kMMMMMMMMMMMMMMMMMMMMMMMMWd.    ",
        " 'XMMMMMMMMMMMMMMMMMMMMMMMMMMk   ",
        "  'XMMMMMMMMMMMMMMMMMMMMMMMMK.   ",
        "    kMMMMMMMMMMMMMMMMMMMMMMd     ",
        "     ;KMMMMMMMWXXWMMMMMMMk.      ",
        "       \"cooc*\"    \"*coo'\"        ",
    ]),
    "linux": (C.YELLOW, [
        "        #####            ",
        "       #######           ",
        "       ##O#O##           ",
        "       #######           ",
        "     ###########         ",
        "    #############        ",
        "   ###############       ",
        "   ################      ",
        "  #################      ",
        " ###################     ",
        "#####################    ",
        "#####################    ",
        "  #################      ",
        "   ###############       ",
        "    ##         ##        ",
    ]),
    "arch": (C.CYAN, [
        "                   -`             ",
        "                  .o+`            ",
        "                 `ooo/            ",
        "                `+oooo:           ",
        "               `+oooooo:          ",
        "               -+oooooo+:         ",
        "             `/:-:++oooo+:        ",
        "            `/++++/+++++++:       ",
        "           `/++++++++++++++:      ",
        "          `/+++ooooooooooooo/`    ",
        "         ./ooosssso++osssssso+`   ",
        "        .oossssso-````/ossssss+`  ",
        "       -osssssso.      :ssssssso. ",
        "      :osssssss/        osssso+++.",
        "     /ossssssss/        +ssssooo/-",
        "   `/ossssso+/:-        -:/+osssso",
        "  `+sso+:-`                 `.-/+o",
        " `++:.                           `",
    ]),
    "ubuntu": (C.RED, [
        "             .-/+oossssoo+/-.       ",
        "         `:+ssssssssssssssssss+:`   ",
        "       -+ssssssssssssssssssyyssss+- ",
        "     .ossssssssssssssssssdMMMNysssso",
        "    /sssssssssss\"hdmmNNmmyNMMMMhsss/",
        "   +sssssssss\"hm           yNMMMMhs+",
        "  /ssssssss\"hNMMM          \"MMMMhssh",
        " .ssssssss\"dMMMNh           \"NMMd  s",
        " +ssss\"hhhyNMMNyy          y\"hMMy ss",
        " oss\"yNMMMNyMMh                MMy h",
        " oss\"yNMMMNyMMh                MMy h",
        " +ssss\"hhhyNMMNyy          y\"hMMy ss",
        " .ssssssss\"dMMMNh           \"NMMd  s",
        "  /ssssssss\"hNMMM          \"MMMMhssh",
        "   +sssssssss\"hm           yNMMMMhs+",
        "    /sssssssssss\"hdmmNNmmyNMMMMhsss/",
        "     .ossssssssssssssssssdMMMNysssso",
        "       -+sssssssssssssssssyyyssss+- ",
        "         `:+ssssssssssssssssss+:`   ",
        "             .-/+oossssoo+/-.       ",
    ]),
    "debian": (C.RED, [
        "       _,met$$$$$gg.           ",
        "    ,g$$$$$$$$$$$$$$$P.        ",
        "  ,g$$P\"     \"\"\"Y$$.\".         ",
        " ,$$P'              `$$$.      ",
        "',$$P       ,ggs.     `$$b:    ",
        "`d$$'     ,$P\"'   .    $$$     ",
        " $$P      d$'     ,    $$P     ",
        " $$:      $$.   -    ,d$$'     ",
        " $$;      Y$b._   _,d$P'       ",
        " Y$$.    `.`\"Y$$$$P\"'          ",
        " `$$b      \"-.__               ",
        "  `Y$$                         ",
        "   `Y$$.                       ",
        "     `$$b.                     ",
        "       `Y$$b.                  ",
        "          `\"Y$b._              ",
        "              `\"\"\"\"            ",
    ]),
    "fedora": (C.BLUE, [
        "          /:-------------:\\    ",
        "       :-------------------::   ",
        "     :-----------/shhOHbmp---:\\ ",
        "   /-----------omMMMNNNMMD  ---:",
        "  :-----------sMMMMNMNMP.    ---",
        " :-----------:MMMdP-------    --",
        ",------------:MMMd--------    ---",
        ":------------:MMMd-------    .--",
        ":----    oNMMMMMMMMMNho     .---",
        ":--     .+shhhMMMmhhy++   .-----",
        ":-    -------:MMMd--------------",
        ":-   --------/MMMd-------------:",
        ":-    ------/hMMMy------------: ",
        ":-- :dMNdhhdNMMNo------------;  ",
        ":---:sdNMMMMNds:------------:   ",
        ":------:://:-------------::     ",
        ":---------------------://       ",
    ]),
    "alpine": (C.BLUE, [
        "       .hddddddddddddddddddddddh.   ",
        "      :dddddddddddddddddddddddddd:  ",
        "     /dddddddddddddddddddddddddddd/ ",
        "    +dddddddddddddddddddddddddddddd+",
        "  `sdddddddddddddddddddddddddddddddd",
        " `ydddddddddddd++hdddddddddddddddddd",
        " .hddddddddddd+`  `+ddddh:-sdddddddd",
        " odddddddddddh`    `hdddh   `oddddhh",
        ":hddddddddddh`      `hddh    `ohdh-:",
        "ohddddddddddh`        `h-      `:- :",
        "hddddddddddhy.                     /",
        "ddddddddhhhhhho/-                  o",
        "ddddddhhhhhhhhhhhhy+-`              ",
        "dddddhhhhhhhhhhhhhhhhhs/.           ",
        "ddddhhhhhhhhhhhhhhhhhhhhhd:         ",
        "dddhhhhhhhhhhhhhhhhhhhhhhhdd        ",
    ]),
    "raspbian": (C.RED, [
        "    .~~.   .~~.       ",
        "   '. \\ ' ' / .'      ",
        "    .~ .~~~..~.       ",
        "   : .~.'~'.~. :      ",
        "  ~ (   ) (   ) ~     ",
        " ( : '~'.~.'~' : )    ",
        "  ~ .~ (   ) ~. ~     ",
        "   (  : '~' :  )      ",
        "    '~ .~~~. ~'       ",
        "        '~'           ",
    ]),
    "android": (C.GREEN, [
        "         -o          o-          ",
        "          +hydNNNNdyh+           ",
        "        +mMMMMMMMMMMMMm+         ",
        "      `dMM--m''MMMMM''m--MMd`    ",
        "      hMMMMMMMMMMMMMMMMMMMMh     ",
        "  ..  yyyyyyyyyyyyyyyyyyyy  ..   ",
        ".mMMm`MMMMMMMMMMMMMMMMMMMM`mMMm. ",
        ":MMMM-MMMMMMMMMMMMMMMMMMMM-MMMM: ",
        ":MMMM-MMMMMMMMMMMMMMMMMMMM-MMMM: ",
        ":MMMM-MMMMMMMMMMMMMMMMMMMM-MMMM: ",
        ":MMMM-MMMMMMMMMMMMMMMMMMMM-MMMM: ",
        "-MMMM-MMMMMMMMMMMMMMMMMMMM-MMMM- ",
        " +yy+ MMMMMMMMMMMMMMMMMMMM +yy+  ",
        "      mMMMMMMMMMMMMMMMMMMm       ",
        "      `/++MMMMh++hMMMM++/`       ",
        "          MMMMo  oMMMM           ",
        "          MMMMo  oMMMM           ",
        "          oNMm-  -mMNs           ",
    ]),
    "ios": (C.WHITE, [
        "          .8.                    ",
        "         .888.                   ",
        "        :88888.                  ",
        "       . `88888.                 ",
        "      .8. `88888.                ",
        "     .8`8. `88888.               ",
        "    .8' `8. `88888.              ",
        "   .8'   `8. `88888.             ",
        "  .888888888. `88888.            ",
        " .8'       `8. `88888.           ",
        ".8'         `8. `88888.          ",
    ]),
    "wsl": (C.MAGENTA, [
        "                                 ",
        "      __        ______ _         ",
        "      \\ \\      / / ___| |        ",
        "       \\ \\ /\\ / /\\___ \\ |        ",
        "        \\ V  V /  ___) | |___    ",
        "         \\_/\\_/  |____/|_____|   ",
        "                                 ",
        "    Windows Subsystem for Linux  ",
        "                                 ",
    ]),
    "chromeos": (C.YELLOW, [
        "             .,:loool:,.            ",
        "         .,coooooooooooooc,.        ",
        "      .,lllllllllllllllllllll,.     ",
        "     ;ccccccccccccccccccccccccc;    ",
        "   ,ooc::::::::okO000000kx;:::::ooo,",
        "  ,ooc:::::::lkOOO0OO0OOOkc:::::::oo",
        "  cll:::::::okOOOdcccc:dxOOOd:::::ll",
        "  cll:::::::dOOOd:::::::lOOO::::::ll",
        "  cll:::::::dOOOd:::::::oOOO::::::ll",
        "  cll:::::::okOOOxoc:::ckOOOk:::::ll",
        "  ,ool:::::::okOOOOOOOOOOOOk::::::lo",
        "   ,ool::::::::cdkOOOOOOOOd:::::::oo",
        "    ;cccc;::::::::::::::::::::::cc; ",
        "      .,coooooooooooooooooooooc,.   ",
        "         .,;loooooooooooool;,.      ",
    ]),
    "bsd": (C.RED, [
        "      ,        ,           ",
        "     /(        )`          ",
        "     \\ \\___   / |          ",
        "     /- _  `-/  '          ",
        "    (/\\/ \\ \\   /\\          ",
        "    / /   | `    \\         ",
        "    O O   ) /    |         ",
        "    `-^--'`<     '         ",
        "   (_.)  _  )   /          ",
        "    `.___/`    /           ",
        "      `-----' /            ",
    ]),
    "haiku": (C.YELLOW, [
        "                       :dc'     ",
        "                    'ck0d        ",
        "                  .;cx0KKo       ",
        "             .,;:lxKKKKKKx       ",
        "         ..,;:cdkKKKKKKKKK,      ",
        "      .';okKKKKKKKKKKKKKKK'      ",
        "    ;ldkKKKKKKKKKKKKKKKKKK,      ",
        "   xKKKKKKKKKKKKKKKKKKKKK;       ",
        "  ;KKKKKKKKKKKKKKKKKKKK0c        ",
        "  cKKKKKKKKKKKKKKKKKKx;          ",
    ]),
    "solaris": (C.YELLOW, [
        "                                       ",
        "       .   .;   -.                     ",
        "  .   : :  ::    ; .   .               ",
        "  .   '.'   '   .' .'                  ",
        "    .                                  ",
        "    .          --                      ",
        "  -- '         ::                      ",
        "  ::            :                      ",
        "                  :    .               ",
        "                       --              ",
        "  Oracle Solaris                       ",
    ]),
    "unknown": (C.WHITE, [
        "    .--.       ",
        "   |o_o |      ",
        "   |:_/ |      ",
        "  //   \\ \\     ",
        " (|     | )    ",
        "/'\\_   _/`\\    ",
        "\\___)=(___/    ",
    ]),
}
LOGOS["cygwin"] = LOGOS["windows"]
# Linux distro fallbacks
for _alias, _fallback in [
    ("linuxmint", "ubuntu"), ("manjaro", "arch"), ("centos", "fedora"),
    ("rhel", "fedora"), ("nixos", "linux"), ("gentoo", "linux"),
    ("opensuse", "linux"),
]:
    LOGOS.setdefault(_alias, LOGOS[_fallback])


# --------------------------------------------------------------------------- #
# Info gatherers                                                              #
# --------------------------------------------------------------------------- #
def get_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return platform.node() or "?"


def get_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER") or os.environ.get("USERNAME") or "?"


def get_os(detected: str) -> str:
    if detected == "windows":
        return f"Windows {platform.release()} ({platform.version()})"
    if detected == "macos":
        try:
            mac, _, _ = platform.mac_ver()
            return f"macOS {mac}" if mac else "macOS"
        except Exception:
            return "macOS"
    if detected in {"linux", "wsl", "arch", "ubuntu", "debian", "fedora",
                    "alpine", "raspbian", "linuxmint", "manjaro", "centos",
                    "rhel", "nixos", "gentoo", "opensuse", "chromeos"}:
        rel = _read_os_release()
        return rel.get("PRETTY_NAME") or rel.get("NAME") or f"Linux {platform.release()}"
    if detected == "android":
        v = _run(["getprop", "ro.build.version.release"]) or "?"
        return f"Android {v}"
    if detected == "ios":
        return f"iOS {platform.release()}"
    if detected == "bsd":
        return f"{platform.system()} {platform.release()}"
    if detected == "solaris":
        return f"Solaris {platform.release()}"
    return f"{platform.system()} {platform.release()}"


def get_kernel() -> str:
    return f"{platform.system()} {platform.release()}"


def get_arch() -> str:
    return platform.machine() or "?"


def get_cpu(detected: str) -> str:
    if detected in {"linux", "android", "wsl", "arch", "ubuntu", "debian",
                    "fedora", "alpine", "raspbian", "linuxmint", "manjaro",
                    "centos", "rhel", "nixos", "gentoo", "opensuse", "chromeos"}:
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith(("model name", "Hardware", "Processor")):
                        return line.split(":", 1)[1].strip()
        except Exception:
            pass
    if detected == "macos":
        n = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if n:
            return n
    if detected == "windows":
        n = os.environ.get("PROCESSOR_IDENTIFIER", "")
        if n:
            return n
    return platform.processor() or platform.machine() or "?"


def get_cpu_cores() -> str:
    n = os.cpu_count()
    return str(n) if n else "?"


def _proc_cpu_times() -> tuple[int, int]:
    with open("/proc/stat") as f:
        line = f.readline().split()
    times = list(map(int, line[1:]))
    idle = times[3] + (times[4] if len(times) > 4 else 0)
    total = sum(times)
    return idle, total


def get_cpu_usage(detected: str) -> str:
    try:
        if detected in {"linux", "android", "wsl", "arch", "ubuntu", "debian",
                        "fedora", "alpine", "raspbian", "linuxmint", "manjaro",
                        "centos", "rhel", "nixos", "gentoo", "opensuse",
                        "chromeos"}:
            i1, t1 = _proc_cpu_times()
            time.sleep(0.25)
            i2, t2 = _proc_cpu_times()
            di, dt = i2 - i1, t2 - t1
            if dt > 0:
                return f"{100.0 * (1 - di / dt):.1f}%"
        elif detected == "windows":
            class FT(ctypes.Structure):
                _fields_ = [("lo", ctypes.c_uint), ("hi", ctypes.c_uint)]

            def ft_int(ft):
                return (ft.hi << 32) | ft.lo

            i1, k1, u1 = FT(), FT(), FT()
            ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(i1), ctypes.byref(k1), ctypes.byref(u1))
            time.sleep(0.25)
            i2, k2, u2 = FT(), FT(), FT()
            ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(i2), ctypes.byref(k2), ctypes.byref(u2))
            idle = ft_int(i2) - ft_int(i1)
            kernel = ft_int(k2) - ft_int(k1)
            user = ft_int(u2) - ft_int(u1)
            total = kernel + user
            if total > 0:
                return f"{100.0 * (1 - idle / total):.1f}%"
        elif detected in ("macos", "ios"):
            out = _run(["top", "-l", "2", "-n", "0"], timeout=4)
            ms = re.findall(
                r"CPU usage:\s*([\d.]+)% user,\s*([\d.]+)% sys", out)
            if ms:
                u, s = float(ms[-1][0]), float(ms[-1][1])
                return f"{u + s:.1f}%"
    except Exception:
        pass
    return "?"


def get_gpu(detected: str) -> str:
    try:
        if detected in {"linux", "wsl", "arch", "ubuntu", "debian", "fedora",
                        "alpine", "raspbian", "linuxmint", "manjaro", "centos",
                        "rhel", "nixos", "gentoo", "opensuse", "chromeos"}:
            out = _run(["lspci"])
            for line in out.splitlines():
                if "VGA" in line or "3D" in line or "Display" in line:
                    if ":" in line:
                        return line.split(":", 2)[-1].strip()
        elif detected == "macos":
            out = _run(["system_profiler", "SPDisplaysDataType"], timeout=4)
            m = re.search(r"Chipset Model:\s*(.+)", out)
            if m:
                return m.group(1).strip()
        elif detected == "windows":
            out = _run([
                "powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_VideoController | "
                "Select-Object -ExpandProperty Name",
            ], timeout=4)
            if out:
                return out.splitlines()[0].strip()
    except Exception:
        pass
    return ""


def get_memory(detected: str) -> str:
    try:
        if detected in {"linux", "android", "wsl", "arch", "ubuntu", "debian",
                        "fedora", "alpine", "raspbian", "linuxmint", "manjaro",
                        "centos", "rhel", "nixos", "gentoo", "opensuse",
                        "chromeos"}:
            mem = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        mem[k.strip()] = v.strip()
            total = int(mem["MemTotal"].split()[0])
            avail = int(mem.get("MemAvailable", "0 kB").split()[0])
            used = total - avail
            return f"{used // 1024} / {total // 1024} MiB ({100 * used // total}%)"
        if detected == "windows":
            class MS(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            ms = MS()
            ms.dwLength = ctypes.sizeof(ms)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                total = ms.ullTotalPhys // (1024 * 1024)
                used = (ms.ullTotalPhys - ms.ullAvailPhys) // (1024 * 1024)
                pct = 100 * used // max(total, 1)
                return f"{used} / {total} MiB ({pct}%)"
        if detected in {"macos", "ios", "bsd"}:
            total_b = _run(["sysctl", "-n", "hw.memsize"]) or _run(
                ["sysctl", "-n", "hw.physmem"])
            if total_b.isdigit():
                total_mib = int(total_b) // (1024 * 1024)
                # Used: parse vm_stat
                vm = _run(["vm_stat"])
                page_size = 4096
                m = re.search(r"page size of (\d+)", vm)
                if m:
                    page_size = int(m.group(1))
                free_pages = 0
                for k in ("Pages free", "Pages speculative"):
                    m = re.search(rf"{k}:\s+(\d+)", vm)
                    if m:
                        free_pages += int(m.group(1))
                if free_pages:
                    free_mib = free_pages * page_size // (1024 * 1024)
                    used_mib = total_mib - free_mib
                    pct = 100 * used_mib // max(total_mib, 1)
                    return f"{used_mib} / {total_mib} MiB ({pct}%)"
                return f"{total_mib} MiB total"
    except Exception:
        pass
    return "?"


def get_uptime(detected: str) -> str:
    try:
        if detected in {"linux", "android", "wsl", "arch", "ubuntu", "debian",
                        "fedora", "alpine", "raspbian", "linuxmint", "manjaro",
                        "centos", "rhel", "nixos", "gentoo", "opensuse",
                        "chromeos"}:
            with open("/proc/uptime") as f:
                seconds = float(f.read().split()[0])
            return _fmt_uptime(seconds)
        if detected == "windows":
            ms = ctypes.windll.kernel32.GetTickCount64()
            return _fmt_uptime(ms / 1000.0)
        if detected in {"macos", "ios", "bsd"}:
            out = _run(["sysctl", "-n", "kern.boottime"])
            m = re.search(r"sec = (\d+)", out)
            if m:
                return _fmt_uptime(time.time() - int(m.group(1)))
    except Exception:
        pass
    return "?"


def _fmt_uptime(seconds: float) -> str:
    d = timedelta(seconds=int(seconds))
    days, rem = divmod(d.total_seconds(), 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{int(days)}d")
    if hours:
        parts.append(f"{int(hours)}h")
    parts.append(f"{int(mins)}m")
    return " ".join(parts)


def get_shell() -> str:
    s = os.environ.get("SHELL") or os.environ.get("ComSpec") or ""
    return os.path.basename(s) if s else "?"


def get_terminal() -> str:
    if os.environ.get("WT_SESSION"):
        return "Windows Terminal"
    for k in ("TERM_PROGRAM", "TERMINAL_EMULATOR", "TERM"):
        v = os.environ.get(k)
        if v:
            return v
    return ""


def get_disk() -> str:
    try:
        path = os.environ.get("HOME", os.environ.get("USERPROFILE", "/"))
        u = shutil.disk_usage(path)
        used = u.used / (1024 ** 3)
        total = u.total / (1024 ** 3)
        pct = int(100 * u.used / max(u.total, 1))
        return f"{used:.1f} / {total:.1f} GiB ({pct}%)"
    except Exception:
        return "?"


def get_battery(detected: str) -> str:
    try:
        if detected in {"linux", "android", "wsl", "arch", "ubuntu", "debian",
                        "fedora", "alpine", "raspbian", "linuxmint", "manjaro",
                        "centos", "rhel", "nixos", "gentoo", "opensuse",
                        "chromeos"}:
            base = "/sys/class/power_supply"
            if os.path.isdir(base):
                for d in sorted(os.listdir(base)):
                    cap = os.path.join(base, d, "capacity")
                    stat = os.path.join(base, d, "status")
                    if os.path.exists(cap):
                        with open(cap) as f:
                            pct = f.read().strip()
                        s = ""
                        if os.path.exists(stat):
                            with open(stat) as f:
                                s = f.read().strip()
                        return f"{pct}% [{s}]" if s else f"{pct}%"
        elif detected == "windows":
            class SPS(ctypes.Structure):
                _fields_ = [
                    ("ACLineStatus", ctypes.c_byte),
                    ("BatteryFlag", ctypes.c_byte),
                    ("BatteryLifePercent", ctypes.c_byte),
                    ("SystemStatusFlag", ctypes.c_byte),
                    ("BatteryLifeTime", ctypes.c_ulong),
                    ("BatteryFullLifeTime", ctypes.c_ulong),
                ]

            sps = SPS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)):
                pct = sps.BatteryLifePercent & 0xFF
                ac = sps.ACLineStatus & 0xFF
                if pct == 255:
                    return ""
                state = "AC" if ac == 1 else "Battery"
                return f"{pct}% [{state}]"
        elif detected == "macos":
            out = _run(["pmset", "-g", "batt"])
            m = re.search(r"(\d+)%;\s*([\w ]+);", out)
            if m:
                return f"{m.group(1)}% [{m.group(2).strip()}]"
            m = re.search(r"(\d+)%", out)
            if m:
                return f"{m.group(1)}%"
    except Exception:
        pass
    return ""


def get_wifi(detected: str) -> str:
    try:
        if detected in {"linux", "wsl", "arch", "ubuntu", "debian", "fedora",
                        "alpine", "raspbian", "linuxmint", "manjaro", "centos",
                        "rhel", "nixos", "gentoo", "opensuse", "chromeos"}:
            out = _run(["nmcli", "-t", "-f", "active,ssid,signal", "dev", "wifi"])
            for line in out.splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and parts[0].lower() == "yes":
                    ssid, sig = parts[1], parts[2]
                    return f"{ssid} ({sig}%)"
            ssid = _run(["iwgetid", "-r"])
            if ssid:
                return ssid
        elif detected == "android":
            out = _run(["termux-wifi-connectioninfo"])
            try:
                d = json.loads(out)
                ssid = (d.get("ssid") or "").strip('"')
                rssi = d.get("rssi")
                if ssid:
                    return f"{ssid} ({rssi} dBm)" if rssi is not None else ssid
            except Exception:
                pass
        elif detected == "windows":
            out = _run(["netsh", "wlan", "show", "interfaces"])
            ssid = re.search(r"^\s*SSID\s*:\s*(.+)$", out, re.M)
            sig = re.search(r"Signal\s*:\s*(\d+%)", out)
            if ssid:
                s = ssid.group(1).strip()
                return f"{s} ({sig.group(1)})" if sig else s
        elif detected == "macos":
            airport = ("/System/Library/PrivateFrameworks/Apple80211.framework/"
                       "Versions/Current/Resources/airport")
            out = _run([airport, "-I"])
            ssid = re.search(r"^\s*SSID:\s*(.+)$", out, re.M)
            rssi = re.search(r"agrCtlRSSI:\s*(-?\d+)", out)
            if ssid:
                s = ssid.group(1).strip()
                return f"{s} ({rssi.group(1)} dBm)" if rssi else s
    except Exception:
        pass
    return ""


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        try:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return ""


def get_resolution(detected: str) -> str:
    try:
        if detected == "windows":
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            return f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
        if detected in {"linux", "arch", "ubuntu", "debian", "fedora",
                        "alpine", "raspbian", "linuxmint", "manjaro", "centos",
                        "rhel", "nixos", "gentoo", "opensuse", "chromeos"}:
            out = _run(["xrandr", "--current"])
            m = re.search(r"current\s+(\d+\s*x\s*\d+)", out)
            if m:
                return m.group(1).replace(" ", "")
        if detected == "macos":
            out = _run(["system_profiler", "SPDisplaysDataType"], timeout=4)
            m = re.search(r"Resolution:\s*(\d+ x \d+)", out)
            if m:
                return m.group(1).replace(" ", "")
    except Exception:
        pass
    return ""


def get_de(detected: str) -> str:
    if detected in {"linux", "wsl", "arch", "ubuntu", "debian", "fedora",
                    "alpine", "raspbian", "linuxmint", "manjaro", "centos",
                    "rhel", "nixos", "gentoo", "opensuse", "chromeos"}:
        return (os.environ.get("XDG_CURRENT_DESKTOP")
                or os.environ.get("DESKTOP_SESSION") or "")
    return ""


def get_load(detected: str) -> str:
    if detected == "windows":
        return ""
    try:
        a, b, c = os.getloadavg()
        return f"{a:.2f} {b:.2f} {c:.2f}"
    except Exception:
        return ""


def get_packages(detected: str) -> str:
    parts = []
    candidates = {
        "dpkg": ["dpkg-query", "-f", ".\n", "-W"],
        "rpm": ["rpm", "-qa"],
        "pacman": ["pacman", "-Qq"],
        "apk": ["apk", "info"],
        "brew": ["brew", "list", "-1"],
        "flatpak": ["flatpak", "list"],
        "snap": ["snap", "list"],
    }
    for name, cmd in candidates.items():
        if shutil.which(cmd[0]):
            out = _run(cmd, timeout=3)
            if out:
                n = len(out.strip().splitlines())
                # snap/flatpak/brew include a header; subtract one if obvious
                if name in {"flatpak", "snap"} and n > 0:
                    n -= 1
                parts.append(f"{n} ({name})")
    return ", ".join(parts)


def get_locale_info() -> str:
    try:
        loc = locale.getlocale()[0]
        if loc:
            return loc
    except Exception:
        pass
    return os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")


def get_python() -> str:
    return f"{platform.python_implementation()} {platform.python_version()}"


def get_ci() -> str:
    if os.environ.get("GITHUB_ACTIONS"):
        return f"GitHub Actions ({os.environ.get('RUNNER_OS', '?')})"
    if os.environ.get("CI"):
        return "CI"
    return ""


# --------------------------------------------------------------------------- #
# Public helper used by Kivy wrapper                                          #
# --------------------------------------------------------------------------- #
def collect(detected: str | None = None) -> list[tuple[str, str]]:
    detected = detected or detect_os()
    fields = [
        ("OS",        get_os(detected)),
        ("Host",      get_hostname()),
        ("User",      get_user()),
        ("Kernel",    get_kernel()),
        ("Arch",      get_arch()),
        ("Uptime",    get_uptime(detected)),
        ("Shell",     get_shell()),
        ("Terminal",  get_terminal()),
        ("DE",        get_de(detected)),
        ("Resolution",get_resolution(detected)),
        ("CPU",       get_cpu(detected)),
        ("Cores",     get_cpu_cores()),
        ("CPU Use",   get_cpu_usage(detected)),
        ("GPU",       get_gpu(detected)),
        ("Memory",    get_memory(detected)),
        ("Disk",      get_disk()),
        ("Battery",   get_battery(detected)),
        ("WiFi",      get_wifi(detected)),
        ("Local IP",  get_local_ip()),
        ("Load",      get_load(detected)),
        ("Packages",  get_packages(detected)),
        ("Locale",    get_locale_info()),
        ("Python",    get_python()),
    ]
    ci = get_ci()
    if ci:
        fields.append(("CI", ci))
    return [(k, v) for k, v in fields if v]


# --------------------------------------------------------------------------- #
# Render                                                                      #
# --------------------------------------------------------------------------- #
def render(detected: str) -> None:
    color, logo = LOGOS.get(detected, LOGOS["unknown"])
    user = get_user()
    host = get_hostname()
    info = collect(detected)

    header = f"{C.B}{color}{user}{C.R}@{C.B}{color}{host}{C.R}"
    sep = "-" * (len(user) + len(host) + 1)
    lines = [header, sep] + [
        f"{C.B}{color}{k}{C.R}: {v}" for k, v in info
    ]

    pad = max(len(l) for l in logo) + 2
    n = max(len(logo), len(lines))
    for i in range(n):
        left = logo[i] if i < len(logo) else ""
        right = lines[i] if i < len(lines) else ""
        print(f"{color}{left:<{pad}}{C.R}{right}")


def main() -> int:
    enable_ansi_on_windows()
    detected = detect_os()
    render(detected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
