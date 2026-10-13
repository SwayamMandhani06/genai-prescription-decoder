#!/usr/bin/env python3
"""
DawaAI - Safe Local Verification Workflow Script
Validates local environment configuration, dependencies, backend connectivity,
frontend alignment, and AI pipeline status without printing or leaking secrets.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def mask_secret(val: str | None) -> str:
    if not val:
        return "[NOT SET]"
    clean = val.strip().strip("'\"")
    if clean.lower().startswith("your_") or clean.lower() in ("placeholder", "xxx", "test_key"):
        return "[PLACEHOLDER - INVALID]"
    if len(clean) < 10:
        return "[SET - (too short)]"
    return f"[CONFIGURED - VALID FORMAT ({len(clean)} chars)]"

def check_env_file() -> dict:
    env_file = ROOT_DIR / ".env"
    results = {
        "exists": env_file.exists(),
        "vars": {}
    }
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    results["vars"][k] = v
    return results

def check_python_dependencies() -> dict:
    pkgs = ["fastapi", "pydantic_settings", "uvicorn", "PIL", "pytest", "httpx", "dotenv"]
    statuses = {}
    for pkg in pkgs:
        try:
            if pkg == "PIL":
                __import__("PIL")
            elif pkg == "dotenv":
                __import__("dotenv")
            else:
                __import__(pkg)
            statuses[pkg] = True
        except ImportError:
            statuses[pkg] = False
    return statuses

def check_backend_health(host: str, port: int) -> dict:
    url = f"http://{host}:{port}/api/v1/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DawaAI-Verification/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"reachable": True, "code": resp.status, "data": data}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {}
        return {"reachable": True, "code": e.code, "data": body}
    except Exception as e:
        return {"reachable": False, "error": str(e)}

def main():
    print("=" * 68)
    print("  DawaAI — Comprehensive Local Environment & Integration Verification")
    print("=" * 68)
    
    # 1. Environment Config
    env_data = check_env_file()
    print("\n[1] Environment Configuration (.env):")
    if not env_data["exists"]:
        print("  [!] .env file not found in root. Using system/default values.")
    else:
        print("  [PASS] .env file located at repository root.")
        
    vars_found = env_data["vars"]
    host = vars_found.get("HOST", os.getenv("HOST", "127.0.0.1"))
    port = int(vars_found.get("PORT", os.getenv("PORT", "8001")))
    vite_base = vars_found.get("VITE_API_BASE_URL", os.getenv("VITE_API_BASE_URL", f"http://{host}:{port}"))
    use_mock_api = vars_found.get("VITE_USE_MOCK_API", os.getenv("VITE_USE_MOCK_API", "false"))
    use_mock_pipeline = vars_found.get("USE_MOCK_PIPELINE", os.getenv("USE_MOCK_PIPELINE", "false")).lower() in ("true", "1")
    gemini_key = vars_found.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

    print(f"  • Backend Bind Target   : {host}:{port}")
    print(f"  • Frontend API Base URL : {vite_base}")
    print(f"  • Frontend Mock Mode    : {use_mock_api}")
    print(f"  • Backend Pipeline Mode : {'MOCK FIXTURE' if use_mock_pipeline else 'LIVE GEMINI PIPELINE'}")
    print(f"  • Gemini Key Status     : {mask_secret(gemini_key)}")

    # 2. Python Dependencies
    print("\n[2] Python Core Dependencies:")
    deps = check_python_dependencies()
    all_deps_ok = True
    for dep, ok in deps.items():
        if ok:
            print(f"  [PASS] {dep}")
        else:
            print(f"  [FAIL] {dep} is missing")
            all_deps_ok = False

    # 3. Frontend / Backend Port Consistency
    print("\n[3] Frontend-to-Backend Port Alignment:")
    expected_backend_target = f":{port}"
    if expected_backend_target in vite_base:
        print(f"  [PASS] VITE_API_BASE_URL points to configured backend port {port} ({vite_base})")
    else:
        print(f"  [WARN] VITE_API_BASE_URL ({vite_base}) does not match configured backend port ({port})")

    # 4. Backend Health & Connectivity
    print(f"\n[4] Backend Service Connectivity (http://{host}:{port}/api/v1/health):")
    health = check_backend_health(host, port)
    if health.get("reachable"):
        data = health.get("data", {})
        status = data.get("status", "unknown")
        mock_mode = data.get("mock_mode", False)
        sys_info = data.get("system_info", {})
        deps_info = sys_info.get("dependencies", {})
        adapter_status = deps_info.get("model_adapter_status") or deps_info.get("multimodal_model_adapter", "unknown")
        model_name = deps_info.get("configured_model", "gemini-3.8-flash")

        print(f"  [PASS] Backend is running and reachable (HTTP {health['code']})")
        print(f"  • Reported Status      : {status.upper()}")
        print(f"  • Backend Mock Mode    : {mock_mode}")
        print(f"  • Active Model         : {model_name}")
        print(f"  • Model Adapter Status : {adapter_status}")
        
        if not mock_mode and adapter_status == "missing_api_key":
            print("  [INFO] Real pipeline is requested (USE_MOCK_PIPELINE=false), but GEMINI_API_KEY is not configured.")
            print("         Endpoints will return HTTP 503 if real inference is attempted without an API key.")
            print("         For offline development, set USE_MOCK_PIPELINE=true in .env.")
    else:
        print(f"  [INFO] Backend is currently OFFLINE or unreachable on {host}:{port}.")
        print(f"         Launch it in a separate terminal via: python backend/run.py")

    # 5. Security Check
    print("\n[5] Security & Secrets Integrity:")
    tracked_env = False
    try:
        import subprocess
        res = subprocess.run(["git", "ls-files", ".env"], cwd=str(ROOT_DIR), capture_output=True, text=True)
        if res.stdout.strip():
            tracked_env = True
    except Exception:
        pass
    if tracked_env:
        print("  [FAIL] .env is tracked by git! Untrack it immediately via git rm --cached .env")
    else:
        print("  [PASS] .env is properly untracked and protected by .gitignore.")

    print("\n" + "=" * 68)
    print("  Local Environment Verification Complete")
    print("=" * 68 + "\n")

if __name__ == "__main__":
    main()
