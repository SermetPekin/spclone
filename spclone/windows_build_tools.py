"""
Windows build tools detection and setup utilities.
Handles Visual Studio, Rtools, and other build environments.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional, List, Dict, Tuple


class WindowsBuildTools:
    """Detect and configure Windows build tools for Python compilation."""
    
    def __init__(self):
        self.detected_tools = {}
        self._scan_build_tools()
    
    def _scan_build_tools(self):
        """Scan for available build tools on Windows."""
        if platform.system() != 'Windows':
            return
        
        self.detected_tools = {
            'visual_studio': self._detect_visual_studio(),
            'rtools': self._detect_rtools(),
            'mingw': self._detect_mingw(),
            'msys2': self._detect_msys2()
        }
    
    def _detect_visual_studio(self) -> Dict:
        """Detect Visual Studio installation."""
        vs_info = {'available': False, 'path': None, 'version': None}
        
        # Check for vswhere.exe
        vswhere_paths = [
            r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
            r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe"
        ]
        
        for vswhere_path in vswhere_paths:
            if os.path.exists(vswhere_path):
                try:
                    result = subprocess.run([
                        vswhere_path, '-latest', '-products', '*', 
                        '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                        '-property', 'installationPath'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        vs_info['available'] = True
                        vs_info['path'] = result.stdout.strip()
                        vs_info['version'] = 'detected'
                        break
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    continue
        
        return vs_info
    
    def _detect_rtools(self) -> Dict:
        """Detect Rtools installation."""
        rtools_info = {'available': False, 'path': None, 'version': None, 'gcc_path': None}
        
        # Common Rtools installation paths
        possible_paths = [
            r"C:\rtools44",
            r"C:\rtools43", 
            r"C:\rtools42",
            r"C:\rtools40",
            r"C:\Rtools",
            r"C:\RBuildTools"
        ]
        
        # Also check PATH for rtools
        path_env = os.environ.get('PATH', '')
        for path_part in path_env.split(os.pathsep):
            if 'rtools' in path_part.lower():
                possible_paths.append(os.path.dirname(path_part))
        
        for rtools_path in possible_paths:
            if os.path.exists(rtools_path):
                # Check for gcc in bin directory
                gcc_paths = [
                    os.path.join(rtools_path, 'mingw64', 'bin', 'gcc.exe'),
                    os.path.join(rtools_path, 'mingw32', 'bin', 'gcc.exe'),
                    os.path.join(rtools_path, 'bin', 'gcc.exe'),
                    os.path.join(rtools_path, 'usr', 'bin', 'gcc.exe')
                ]
                
                for gcc_path in gcc_paths:
                    if os.path.exists(gcc_path):
                        try:
                            # Test gcc
                            result = subprocess.run([gcc_path, '--version'], 
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode == 0:
                                rtools_info['available'] = True
                                rtools_info['path'] = rtools_path
                                rtools_info['gcc_path'] = gcc_path
                                
                                # Extract version
                                version_line = result.stdout.split('\n')[0]
                                if 'gcc' in version_line:
                                    rtools_info['version'] = version_line
                                
                                return rtools_info
                        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                            continue
        
        return rtools_info
    
    def _detect_mingw(self) -> Dict:
        """Detect standalone MinGW installation."""
        mingw_info = {'available': False, 'path': None}
        
        try:
            result = subprocess.run(['gcc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'mingw' in result.stdout.lower():
                mingw_info['available'] = True
                # Try to find the path
                which_result = subprocess.run(['where', 'gcc'], 
                                            capture_output=True, text=True, timeout=5)
                if which_result.returncode == 0:
                    mingw_info['path'] = os.path.dirname(which_result.stdout.strip())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return mingw_info
    
    def _detect_msys2(self) -> Dict:
        """Detect MSYS2 installation."""
        msys2_info = {'available': False, 'path': None}
        
        msys2_paths = [r"C:\msys64", r"C:\msys32"]
        for msys2_path in msys2_paths:
            if os.path.exists(msys2_path):
                gcc_path = os.path.join(msys2_path, 'mingw64', 'bin', 'gcc.exe')
                if os.path.exists(gcc_path):
                    msys2_info['available'] = True
                    msys2_info['path'] = msys2_path
                    break
        
        return msys2_info
    
    def get_available_tools(self) -> List[str]:
        """Get list of available build tools."""
        return [tool for tool, info in self.detected_tools.items() if info.get('available', False)]
    
    def get_recommended_tool(self) -> Optional[str]:
        """Get the recommended build tool to use."""
        available = self.get_available_tools()
        
        # Preference order: Visual Studio > Rtools > MinGW > MSYS2
        preference_order = ['visual_studio', 'rtools', 'mingw', 'msys2']
        
        for preferred in preference_order:
            if preferred in available:
                return preferred
        
        return None
    
    def setup_rtools_environment(self) -> bool:
        """Setup environment variables for Rtools."""
        rtools = self.detected_tools.get('rtools', {})
        if not rtools.get('available'):
            return False
        
        rtools_path = rtools['path']
        gcc_path = rtools['gcc_path']
        
        # Add Rtools to PATH
        bin_dir = os.path.dirname(gcc_path)
        current_path = os.environ.get('PATH', '')
        
        if bin_dir not in current_path:
            os.environ['PATH'] = f"{bin_dir}{os.pathsep}{current_path}"
        
        # Set compiler environment variables
        os.environ['CC'] = gcc_path
        os.environ['CXX'] = gcc_path.replace('gcc.exe', 'g++.exe')
        
        # Set distutils to use mingw32
        os.environ['DISTUTILS_USE_SDK'] = '1'
        os.environ['MSSdk'] = '1'
        
        return True
    
    def print_status_report(self):
        """Print a comprehensive status report of build tools."""
        print("\n" + "="*60)
        print("🔧 WINDOWS BUILD TOOLS STATUS")
        print("="*60)
        
        if not self.detected_tools:
            print("❌ No build tools scan performed (not on Windows)")
            return
        
        available_count = len(self.get_available_tools())
        
        print(f"✅ Found {available_count} build tool(s)")
        print()
        
        # Visual Studio
        vs = self.detected_tools['visual_studio']
        if vs['available']:
            print("🎯 Visual Studio Build Tools: ✅ AVAILABLE")
            print(f"   Path: {vs['path']}")
        else:
            print("🎯 Visual Studio Build Tools: ❌ Not found")
        
        # Rtools
        rtools = self.detected_tools['rtools']
        if rtools['available']:
            print("🔧 Rtools: ✅ AVAILABLE")
            print(f"   Path: {rtools['path']}")
            print(f"   GCC: {rtools['gcc_path']}")
            print(f"   Version: {rtools['version']}")
        else:
            print("🔧 Rtools: ❌ Not found")
        
        # MinGW
        mingw = self.detected_tools['mingw']
        if mingw['available']:
            print("⚙️  MinGW: ✅ AVAILABLE")
            print(f"   Path: {mingw['path']}")
        else:
            print("⚙️  MinGW: ❌ Not found")
        
        # MSYS2
        msys2 = self.detected_tools['msys2']
        if msys2['available']:
            print("🖥️  MSYS2: ✅ AVAILABLE")
            print(f"   Path: {msys2['path']}")
        else:
            print("🖥️  MSYS2: ❌ Not found")
        
        print()
        recommended = self.get_recommended_tool()
        if recommended:
            print(f"💡 Recommended: {recommended.replace('_', ' ').title()}")
        else:
            print("⚠️  No build tools available - some packages may fail to install")
        
        print("="*60)
    
    def print_installation_help(self):
        """Print installation help for missing build tools."""
        print("\n" + "="*60)
        print("📥 BUILD TOOLS INSTALLATION GUIDE")
        print("="*60)
        
        available = self.get_available_tools()
        
        if available:
            print(f"✅ You already have: {', '.join(available)}")
            print("You're all set for most Python packages!")
            print()
        
        print("If you need additional build tools, here are your options:")
        print()
        
        # Visual Studio option
        if 'visual_studio' not in available:
            print("🎯 Option 1: Visual Studio Build Tools (Microsoft Official)")
            print("   • Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
            print("   • Install 'C++ build tools' workload")
            print("   • Include 'Windows 10/11 SDK'")
            print("   • Best compatibility with pip and setuptools")
            print()
        
        # Rtools option
        if 'rtools' not in available:
            print("🔧 Option 2: Rtools (Great for R users)")
            print("   • Download: https://cran.r-project.org/bin/windows/Rtools/")
            print("   • Lightweight GCC toolchain")
            print("   • Perfect if you already use R")
            print("   • Includes make, gcc, g++, and other Unix tools")
            print()
        
        # MSYS2 option
        if 'msys2' not in available:
            print("🖥️  Option 3: MSYS2 (Unix-like environment)")
            print("   • Download: https://www.msys2.org/")
            print("   • Full Unix-like environment")
            print("   • Package manager: pacman -S mingw-w64-x86_64-gcc")
            print("   • Good for complex builds")
            print()
        
        print("💡 Recommendation:")
        if not available:
            print("   For most users: Start with Visual Studio Build Tools")
            print("   For R users: Rtools is perfect and lightweight")
            print("   For developers: MSYS2 provides the most flexibility")
        else:
            print("   You're already set up! Your current tools should work fine.")
        
        print("="*60)


def check_and_setup_windows_build_tools(verbose: bool = False) -> bool:
    """
    Check for Windows build tools and set up the best available option.
    
    Args:
        verbose: Print detailed status information
    
    Returns:
        True if build tools are available and configured
    """
    if platform.system() != 'Windows':
        return True  # Not Windows, assume build tools are available
    
    tools = WindowsBuildTools()
    
    if verbose:
        tools.print_status_report()
    
    available_tools = tools.get_available_tools()
    
    if not available_tools:
        if verbose:
            print("❌ No Windows build tools found")
        return False
    
    recommended = tools.get_recommended_tool()
    
    if recommended == 'rtools':
        if verbose:
            print("🔧 Setting up Rtools environment...")
        success = tools.setup_rtools_environment()
        if verbose and success:
            print("✅ Rtools environment configured")
        return success
    
    # For Visual Studio, MinGW, MSYS2 - they should work without special setup
    if verbose:
        print(f"✅ Using {recommended} for compilation")
    
    return True


def print_windows_build_help():
    """Print comprehensive Windows build help."""
    tools = WindowsBuildTools()
    tools.print_installation_help()