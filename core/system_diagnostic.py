
import os
import sys
import subprocess
import psutil
import platform
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


class SystemDiagnostic:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.diagnostics: Dict[str, Any] = {}

    def run_full_diagnostic(self) -> Dict[str, Any]:
        self.diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.get_system_info(),
            "python_env": self.get_python_env(),
            "openmars_status": self.check_openmars(),
            "workspace_status": self.check_workspaces(),
            "resource_usage": self.get_resource_usage(),
            "network_status": self.check_network()
        }
        return self.diagnostics

    def get_system_info(self) -> Dict[str, str]:
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node()
        }

    def get_python_env(self) -> Dict[str, Any]:
        return {
            "version": sys.version,
            "executable": sys.executable,
            "prefix": sys.prefix,
            "packages": self.get_installed_packages()
        }

    def get_installed_packages(self) -> List[str]:
        try:
            import pkg_resources
            return [f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set]
        except:
            return []

    def check_openmars(self) -> Dict[str, Any]:
        result = {
            "installed": False,
            "path": None,
            "version": None,
            "config_exists": False,
            "gateway_running": False
        }

        try:
            which_result = subprocess.run(
                ["which", "openmars"],
                capture_output=True,
                text=True
            )
            if which_result.returncode == 0:
                result["path"] = which_result.stdout.strip()
                result["installed"] = True

                try:
                    version_result = subprocess.run(
                        ["openmars", "--version"],
                        capture_output=True,
                        text=True
                    )
                    if version_result.returncode == 0:
                        result["version"] = version_result.stdout.strip()
                except:
                    pass
        except:
            pass

        openmars_config = Path.home() / ".openmars"
        result["config_exists"] = openmars_config.exists()

        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'openmars' in cmdline and 'gateway' in cmdline:
                        result["gateway_running"] = True
                        break
                except:
                    pass
        except:
            pass

        return result

    def check_workspaces(self) -> Dict[str, Any]:
        workspaces_dir = self.base_path / "workspaces"
        result = {
            "total": 0,
            "workspaces": []
        }

        if workspaces_dir.exists():
            for ws_dir in workspaces_dir.iterdir():
                if ws_dir.is_dir():
                    ws_info = {
                        "name": ws_dir.name,
                        "path": str(ws_dir),
                        "size_mb": self.get_dir_size(ws_dir),
                        "created": datetime.fromtimestamp(ws_dir.stat().st_ctime).isoformat()
                    }
                    result["workspaces"].append(ws_info)
            result["total"] = len(result["workspaces"])

        return result

    def get_dir_size(self, path: Path) -> float:
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except:
            pass
        return total / (1024 * 1024)

    def get_resource_usage(self) -> Dict[str, Any]:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_mb": psutil.virtual_memory().total / (1024 * 1024),
                "available_mb": psutil.virtual_memory().available / (1024 * 1024),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total_mb": psutil.disk_usage('/').total / (1024 * 1024),
                "free_mb": psutil.disk_usage('/').free / (1024 * 1024),
                "percent": psutil.disk_usage('/').percent
            }
        }

    def check_network(self) -> Dict[str, Any]:
        result = {
            "internet_connected": False,
            "dns_resolves": False,
            "apis_reachable": {}
        }

        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            result["internet_connected"] = True
        except:
            pass

        try:
            socket.gethostbyname("api.openai.com")
            result["dns_resolves"] = True
        except:
            pass

        apis_to_check = [
            ("openai", "https://api.openai.com"),
            ("github", "https://api.github.com")
        ]

        try:
            import requests
            for name, url in apis_to_check:
                try:
                    response = requests.head(url, timeout=5)
                    result["apis_reachable"][name] = response.status_code < 500
                except:
                    result["apis_reachable"][name] = False
        except:
            pass

        return result

    def generate_report(self) -> str:
        diag = self.run_full_diagnostic()
        lines = ["=" * 60, "赛博印钞机 Pro Ultra - 系统诊断报告", "=" * 60, ""]

        lines.append(f"生成时间: {diag['timestamp']}")
        lines.append("")

        lines.append("【系统信息】")
        for k, v in diag['system_info'].items():
            lines.append(f"  {k}: {v}")
        lines.append("")

        lines.append("【Python 环境】")
        lines.append(f"  版本: {diag['python_env']['version']}")
        lines.append(f"  可执行文件: {diag['python_env']['executable']}")
        lines.append("")

        lines.append("【OpenMars 状态】")
        oc = diag['openmars_status']
        lines.append(f"  已安装: {'✅' if oc['installed'] else '❌'}")
        if oc['path']:
            lines.append(f"  路径: {oc['path']}")
        if oc['version']:
            lines.append(f"  版本: {oc['version']}")
        lines.append(f"  配置目录: {'✅' if oc['config_exists'] else '❌'}")
        lines.append(f"  网关运行中: {'✅' if oc['gateway_running'] else '❌'}")
        lines.append("")

        lines.append("【工作区】")
        ws = diag['workspace_status']
        lines.append(f"  总数: {ws['total']}")
        for workspace in ws['workspaces']:
            lines.append(f"  - {workspace['name']}: {workspace['size_mb']:.2f} MB")
        lines.append("")

        lines.append("【资源使用】")
        ru = diag['resource_usage']
        lines.append(f"  CPU: {ru['cpu_percent']}%")
        lines.append(f"  内存: {ru['memory']['percent']}% ({ru['memory']['available_mb']:.0f} MB 可用)")
        lines.append(f"  磁盘: {ru['disk']['percent']}% ({ru['disk']['free_mb']:.0f} MB 可用)")
        lines.append("")

        lines.append("【网络状态】")
        ns = diag['network_status']
        lines.append(f"  互联网连接: {'✅' if ns['internet_connected'] else '❌'}")
        lines.append(f"  DNS 解析: {'✅' if ns['dns_resolves'] else '❌'}")
        for api, reachable in ns['apis_reachable'].items():
            lines.append(f"  {api}: {'✅' if reachable else '❌'}")

        return "\n".join(lines)

