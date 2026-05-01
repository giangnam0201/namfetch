#!/usr/bin/env python3
"""devfetch - a neofetch-like tool that runs on every device Python runs on.

Native: Windows, macOS, Linux.
Mobile: Android (Termux), iOS (a-Shell / Pythonista).
Other:  *BSD, Haiku, Cygwin, WSL.

Standard library only - no pip install required.
"""
from __future__ import annotations

import ctypes
import getpass
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


# --------------------------------------------------------------------------- #
# OS detection                                                                #
# --------------------------------------------------------------------------- #
def detect_os() -> str:
    s = platform.system()
    if s == "Linux":
        if "ANDROID_ROOT" in os.environ or "ANDROID_DATA" in os.environ:
            return "android"
        if os.path.exists("/system/build.prop"):
            return "android"
        if "microsoft" in platform.release().lower() or "WSL_DISTRO_NAME" in os.environ:
            return "wsl"
        return "linux"
    if s == "Darwin":
        m = platform.machine().lower()
        if m.startswith(("iphone", "ipad", "ipod")):
            return "ios"
        if "PYTHONISTA_DOC" in os.environ or "/var/mobile" in os.path.expanduser("~"):
            return "ios"
        return "macos"
    if s == "Windows":
        return "windows"
    if s.endswith("BSD"):
        return "bsd"
    if s == "Haiku":
        return "haiku"
    if s.startswith("CYGWIN"):
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


# --------------------------------------------------------------------------- #
# Info gatherers                                                              #
# --------------------------------------------------------------------------- #
def _run(cmd: list[str], timeout: float = 2.0) -> str:
    try:
        out = subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL, timeout=timeout
        )
        return out.decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


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
        v = platform.version()
        return f"Windows {platform.release()} ({v})"
    if detected == "macos":
        try:
            mac, _, _ = platform.mac_ver()
            return f"macOS {mac}" if mac else "macOS"
        except Exception:
            return "macOS"
    if detected == "linux" or detected == "wsl":
        # Try /etc/os-release
        try:
            with open("/etc/os-release") as f:
                kv = dict(
                    line.strip().split("=", 1)
                    for line in f
                    if "=" in line and not line.startswith("#")
                )
            name = kv.get("PRETTY_NAME", kv.get("NAME", "Linux")).strip('"')
            return name
        except Exception:
            return f"Linux {platform.release()}"
    if detected == "android":
        v = _run(["getprop", "ro.build.version.release"]) or "?"
        return f"Android {v}"
    if detected == "ios":
        return f"iOS {platform.release()}"
    if detected == "bsd":
        return f"{platform.system()} {platform.release()}"
    return f"{platform.system()} {platform.release()}"


def get_kernel() -> str:
    return f"{platform.system()} {platform.release()}"


def get_arch() -> str:
    return platform.machine() or "?"


def get_cpu(detected: str) -> str:
    # Try platform-specific sources first
    if detected in ("linux", "android", "wsl"):
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


def get_memory(detected: str) -> str:
    try:
        if detected in ("linux", "android", "wsl"):
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = parts[1].strip()
            total_kb = int(meminfo["MemTotal"].split()[0])
            avail_kb = int(meminfo.get("MemAvailable", "0 kB").split()[0])
            used_kb = total_kb - avail_kb
            return f"{used_kb // 1024} MiB / {total_kb // 1024} MiB"
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
                return f"{used} MiB / {total} MiB"
        if detected in ("macos", "ios", "bsd"):
            total_b = _run(["sysctl", "-n", "hw.memsize"]) or _run(
                ["sysctl", "-n", "hw.physmem"]
            )
            if total_b.isdigit():
                total_mib = int(total_b) // (1024 * 1024)
                return f"? MiB / {total_mib} MiB"
    except Exception:
        pass
    return "?"


def get_uptime(detected: str) -> str:
    try:
        if detected in ("linux", "android", "wsl"):
            with open("/proc/uptime") as f:
                seconds = float(f.read().split()[0])
            return _fmt_uptime(seconds)
        if detected == "windows":
            ms = ctypes.windll.kernel32.GetTickCount64()
            return _fmt_uptime(ms / 1000.0)
        if detected in ("macos", "ios", "bsd"):
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
    for k in ("TERM_PROGRAM", "WT_SESSION", "TERM"):
        v = os.environ.get(k)
        if v:
            return v if k != "WT_SESSION" else "Windows Terminal"
    return "?"


def get_disk() -> str:
    try:
        path = os.environ.get("HOME", os.environ.get("USERPROFILE", "/"))
        usage = shutil.disk_usage(path)
        used_gb = usage.used / (1024**3)
        total_gb = usage.total / (1024**3)
        return f"{used_gb:.1f} GiB / {total_gb:.1f} GiB"
    except Exception:
        return "?"


def get_python() -> str:
    return f"{platform.python_implementation()} {platform.python_version()}"


def get_ci() -> str:
    if os.environ.get("GITHUB_ACTIONS"):
        return f"GitHub Actions ({os.environ.get('RUNNER_OS', '?')})"
    if os.environ.get("CI"):
        return "CI"
    return ""


# --------------------------------------------------------------------------- #
# Render                                                                      #
# --------------------------------------------------------------------------- #
def render(detected: str) -> None:
    color, logo = LOGOS.get(detected, LOGOS["unknown"])
    user = get_user()
    host = get_hostname()

    info = [
        ("OS", get_os(detected)),
        ("Host", host),
        ("Kernel", get_kernel()),
        ("Arch", get_arch()),
        ("Uptime", get_uptime(detected)),
        ("Shell", get_shell()),
        ("Terminal", get_terminal()),
        ("CPU", get_cpu(detected)),
        ("Memory", get_memory(detected)),
        ("Disk", get_disk()),
        ("Python", get_python()),
    ]
    ci = get_ci()
    if ci:
        info.append(("CI", ci))

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
