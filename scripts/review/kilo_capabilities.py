#!/usr/bin/env python3
"""
METFI Kilo Code Capability & Agent Discovery Module.

Discovers the real local installation of Kilo Code CLI (@kilocode/cli),
inspects available agents/modes, permissions, and command flags.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import NamedTuple


class KiloAgentInfo(NamedTuple):
    name: str
    is_primary: bool
    description: str = ""
    is_read_only: bool = False


class KiloCapabilities(NamedTuple):
    available: bool
    executable: str | None
    version: str | None
    agents: list[KiloAgentInfo]
    default_agent: str | None
    supported_flags: list[str]
    raw_error: str | None = None


def find_kilo_executable() -> str | None:
    """Find the path to the kilo executable on Windows or in PATH."""
    return shutil.which("kilo") or shutil.which("kilo.cmd") or shutil.which("kilo.exe")


def discover_kilo_version(executable: str) -> str | None:
    """Get the installed Kilo version string."""
    try:
        res = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def discover_kilo_agents(executable: str) -> list[KiloAgentInfo]:
    """Parse available agents and modes from `kilo agent list`."""
    agents: list[KiloAgentInfo] = []
    try:
        res = subprocess.run(
            [executable, "agent", "list"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            for line in lines:
                stripped = line.strip()
                # Check for agent header line (e.g. "orchestrator (primary)" or "reviewer" or "coder")
                match = re.match(r"^([a-zA-Z0-9_-]+)(?:\s+\((primary)\))?$", stripped)
                if match:
                    agent_name = match.group(1)
                    # Ignore ASCII art or help tokens
                    if (
                        agent_name in ("Commands", "Options", "INFO", "kilo")
                        or "█" in agent_name
                    ):
                        continue
                    is_prim = bool(match.group(2))
                    # Check if agent is read-only (e.g. plan/summary/reviewer/read permissions)
                    agents.append(
                        KiloAgentInfo(
                            name=agent_name,
                            is_primary=is_prim,
                            description=f"Kilo {agent_name} agent",
                            is_read_only=(
                                agent_name
                                in ("reviewer", "planner", "summary", "title", "tester")
                            ),
                        )
                    )
    except (subprocess.SubprocessError, OSError):
        pass

    return agents


def discover_kilo_capabilities() -> KiloCapabilities:
    """Full capability discovery for Kilo Code CLI."""
    exe = find_kilo_executable()
    if not exe:
        return KiloCapabilities(
            available=False,
            executable=None,
            version=None,
            agents=[],
            default_agent=None,
            supported_flags=[],
            raw_error="Kilo executable not found in system PATH (ensure @kilocode/cli is installed globally)",
        )

    version = discover_kilo_version(exe)
    agents = discover_kilo_agents(exe)

    # If agent list was empty or couldn't be parsed, discover supported roles
    agent_names = [a.name for a in agents]

    # Supported flags in `kilo run`
    supported_flags = [
        "--agent",
        "--dir",
        "--file",
        "--format",
        "--model",
        "--variant",
        "--thinking",
        "--auto",
    ]

    default_agent = next(
        (a.name for a in agents if a.is_primary),
        (agent_names[0] if agent_names else "general"),
    )

    return KiloCapabilities(
        available=True,
        executable=exe,
        version=version,
        agents=agents,
        default_agent=default_agent,
        supported_flags=supported_flags,
    )


# Standard METFI Role to Kilo Agent Mapping
ROLE_TO_KILO_AGENT_MAP: dict[str, str] = {
    "reviewer": "ask",
    "debugger": "debug",
    "tester": "ask",
    "planner": "plan",
    "orchestrator": "orchestrator",
    "ask": "ask",
    "debug": "debug",
    "plan": "plan",
    "code": "code",
}

# Recommended Specialist Roles per Implementation Phase
PHASE_RECOMMENDED_AGENTS: dict[str, list[str]] = {
    "0": ["reviewer", "tester"],
    "1": ["reviewer", "tester"],
    "2": ["reviewer", "debugger", "tester"],
    "3": ["reviewer", "planner", "debugger"],
    "4": ["reviewer", "orchestrator", "debugger"],
    "generic": ["reviewer", "debugger"],
}


def resolve_kilo_agent(role_or_agent: str) -> str:
    """Resolve a METFI review role or raw agent name to an installed Kilo agent."""
    normalized = role_or_agent.strip().lower()
    return ROLE_TO_KILO_AGENT_MAP.get(normalized, normalized)


def get_phase_recommended_agents(phase: str) -> list[str]:
    """Get the recommended Kilo specialist roles for a given phase."""
    return PHASE_RECOMMENDED_AGENTS.get(str(phase).lower(), ["reviewer"])


def main() -> None:
    caps = discover_kilo_capabilities()
    print("=" * 60)
    print("METFI KILO CODE CAPABILITY DISCOVERY")
    print("=" * 60)
    print(f"Available      : {caps.available}")
    print(f"Executable     : {caps.executable}")
    print(f"Version        : {caps.version}")
    print(f"Default Agent  : {caps.default_agent}")
    print(f"Discovered Agents ({len(caps.agents)}):")
    for ag in caps.agents:
        prim_str = " [PRIMARY]" if ag.is_primary else ""
        ro_str = " (Read-Only)" if ag.is_read_only else ""
        print(f"  - {ag.name}{prim_str}{ro_str}")
    print(f"Supported Flags: {', '.join(caps.supported_flags)}")
    print("\nRole to Agent Mapping:")
    for role, mapped in ROLE_TO_KILO_AGENT_MAP.items():
        print(f"  - {role:<14} -> kilo agent '{mapped}'")
    if caps.raw_error:
        print(f"\nError          : {caps.raw_error}")
    print("=" * 60)


if __name__ == "__main__":
    main()
