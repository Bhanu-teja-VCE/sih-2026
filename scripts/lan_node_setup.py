"""
scripts/lan_node_setup.py
Distributed LAN Compute Node Network Configurator & Health Prober.
Connects Master Edge Workstation to Remote GPU Compute Node over Private Subnet.
Zero WAN Egress.
"""

import sys
import time
import urllib.request
import json
import socket


def get_local_ip() -> str:
    """Gets local machine private IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not send packets, just gets routing table IP
        s.connect(("192.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def probe_remote_ollama_node(remote_ip: str, port: int = 11434, timeout: float = 3.0) -> bool:
    """Tests connection to remote friend's laptop running Ollama / llama.cpp."""
    url = f"http://{remote_ip}:{port}/api/tags"
    print(f"[*] Probing Remote Compute Pod at {url}...")
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                print(f"[+] SUCCESS! Remote node connected on isolated private subnet.")
                print(f"    Available Remote SLMs: {models}")
                return True
    except Exception as e:
        print(f"[-] Node probe failed: {str(e)}")
        print(f"    Fallback: Master station will use local fast inference engine.")
    return False


def main():
    print("=" * 70)
    print("   MRPL SOVEREIGN WORKBENCH — DISTRIBUTED LAN NODE CONFIGURATOR")
    print("=" * 70)
    local_ip = get_local_ip()
    print(f"[*] Master Station Private IP: {local_ip}")
    
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.150"
    probe_remote_ollama_node(target_ip)


if __name__ == "__main__":
    main()
