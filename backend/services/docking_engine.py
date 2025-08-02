"""
分子对接引擎 - 集成成熟的对接、可视化和分析模块
整合 docking_test 目录下的完整分子对接系统
"""

import os
import sys
import logging
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ..core.config import settings
from ..models.exceptions import ProcessingError, FileError
from ..utils.helpers import safe_execute, validate_file_exists

logger = logging.getLogger(__name__)


class ProteinPreprocessor:
    """蛋白质结构预处理器 - 基于成熟的实现"""
    
    def __init__(self):
        self.input_file = None
        self.output_file = None
    
    def fix_protein_structure(self, input_file: Path, output_file: Optional[Path] = None) -> Optional[Path]:
        """
        清理蛋白质结构，移除 ROOT/ENDROOT 标签
        基于 docking_test/molecular_docking.py 的成熟实现
        """
        if output_file is None:
            output_file = input_file.parent / f"{input_file.stem}_receptor.pdbqt"
        
        self.input_file = input_file
        self.output_file = output_file
        
        logger.info(f"Processing protein structure: {input_file}")
        
        try:
            with open(input_file, 'r') as f:
                lines = f.readlines()
            
            # 过滤掉问题行
            filtered_lines = []
            removed_count = 0
            
            for line in lines:
                line_strip = line.strip()
                
                # 移除所有不支持的PDB标签（这些标签在PDBQT格式中不被支持）
                problematic_tags = [
                    'ROOT', 'ENDROOT', 'BRANCH', 'ENDBRANCH', 'TORSDOF',  # 旧的问题标签
                    'HEADER', 'TITLE', 'AUTHOR', 'REVDAT', 'JRNL',         # PDB文件头信息
                    'REMARK', 'SEQRES', 'DBREF', 'SSBOND', 'LINK',        # PDB元数据
                    'CRYST1', 'ORIGX', 'SCALE', 'MTRIX', 'MASTER',        # 晶体学信息
                    'EXPDTA', 'CAVEAT', 'COMPND', 'SOURCE', 'KEYWDS',     # 实验数据信息
                    'CONECT'                                                # 连接信息（Vina不支持）
                ]
                
                # 检查是否包含问题标签
                if any(line_strip.startswith(tag) for tag in problematic_tags):
                    removed_count += 1
                    logger.debug(f"Removed line with tag: {line_strip[:10]}...")
                    continue
                
                # 只保留原子记录和相关的结构信息（移除CONECT，Vina不支持）
                if line_strip.startswith(('ATOM', 'HETATM', 'END', 'TER')) or line_strip == '':
                    # 对原子行进行原子类型检查，完全跳过有问题的原子
                    if line_strip.startswith(('ATOM', 'HETATM')):
                        if self._should_remove_atom(line):
                            removed_count += 1
                            logger.debug(f"Removed problematic atom: {line_strip[:30]}...")
                            continue
                    filtered_lines.append(line)
                else:
                    # 记录但跳过其他未知标签
                    removed_count += 1
                    logger.debug(f"Removed unknown tag: {line_strip[:20]}...")
                    continue
            
            # 写入清理后的文件
            with open(output_file, 'w') as f:
                f.writelines(filtered_lines)
            
            logger.info(f"Cleaned protein structure saved as: {output_file}")
            logger.info(f"Removed {removed_count} problematic lines")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error processing protein: {e}")
            return None
    
    def _should_remove_atom(self, line: str) -> bool:
        """
        检查是否应该移除这个原子行（因为AutoDock Vina不支持）
        """
        try:
            # 获取原子名称和元素符号部分
            atom_name = line[12:16].strip()  # 原子名称
            element = line[76:78].strip() if len(line) > 77 else ""  # 元素符号
            
            # 如果没有元素符号，从原子名称推断
            if not element and atom_name:
                # 从原子名称推断元素（取前1-2个字符）
                if atom_name.startswith(('CL', 'Cl')):
                    element = 'CL'
                elif atom_name.startswith(('BR', 'Br')):
                    element = 'BR'
                elif atom_name.startswith(('FE', 'Fe')):
                    element = 'FE'
                elif atom_name.startswith(('MG', 'Mg')):
                    element = 'MG'
                elif atom_name.startswith(('CA', 'Ca')) and not atom_name.startswith('C'):
                    element = 'CA'
                elif atom_name.startswith(('ZN', 'Zn')):
                    element = 'ZN'
                elif atom_name.startswith(('MN', 'Mn')):
                    element = 'MN'
            
            # AutoDock Vina不支持的原子类型（会导致解析错误）
            problematic_atoms = [
                'Cl', 'CL',   # 氯原子
                'Br', 'BR',   # 溴原子
                'Fe', 'FE',   # 铁原子
                'Mg', 'MG',   # 镁原子
                'Ca', 'CA',   # 钙原子
                'Zn', 'ZN',   # 锌原子
                'Mn', 'MN',   # 锰原子
                'Cu', 'CU',   # 铜原子
                'Ni', 'NI',   # 镍原子
                'Co', 'CO',   # 钴原子
                'Na', 'NA',   # 钠原子
                'K',          # 钾原子
                'I',          # 碘原子
                'Al', 'AL'    # 铝原子
            ]
            
            # 检查原子名称或元素符号是否有问题
            if atom_name in problematic_atoms or element in problematic_atoms:
                logger.debug(f"Will remove problematic atom: {atom_name} / {element}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking atom in line: {e}")
            # 如果解析出错，保留原子（安全起见）
            return False


class MolecularDocker:
    """分子对接器 - 基于 AutoDock Vina 的成熟实现"""
    
    def __init__(self, vina_executable: str = None):
        # 根据项目设置选择 Vina 可执行文件
        if vina_executable is None:
            vina_executable = str(project_root / "vina")
        
        self.vina_executable = vina_executable
        self.receptor_file = None
        self.ligand_file = None
        self.output_file = None
        self.config = {
            'center_x': 2.8,
            'center_y': 23.3, 
            'center_z': 14.1,
            'size_x': 25.0,
            'size_y': 25.0,
            'size_z': 25.0,
            'exhaustiveness': 2,
            'num_modes': 2,
            'energy_range': 3
        }
    
    def set_files(self, receptor_file: Path, ligand_file: Path, output_file: Path = None):
        """设置输入和输出文件"""
        self.receptor_file = receptor_file
        self.ligand_file = ligand_file
        self.output_file = output_file or Path("docking_results.pdbqt")
    
    def set_search_space(self, center_x: float, center_y: float, center_z: float, 
                        size_x: float = 20, size_y: float = 20, size_z: float = 20):
        """定义对接搜索空间"""
        self.config.update({
            'center_x': center_x,
            'center_y': center_y,
            'center_z': center_z,
            'size_x': size_x,
            'size_y': size_y,
            'size_z': size_z
        })
    
    def run_docking(self) -> bool:
        """执行分子对接"""
        if not all([self.receptor_file, self.ligand_file]):
            logger.error("Receptor and ligand files must be set")
            return False
        
        # 检查文件是否存在
        if not self.receptor_file.exists():
            logger.error(f"Receptor file not found: {self.receptor_file}")
            return False
            
        if not self.ligand_file.exists():
            logger.error(f"Ligand file not found: {self.ligand_file}")
            return False
        
        # 检查 Vina 可执行文件
        if not Path(self.vina_executable).exists():
            logger.error(f"Vina executable not found: {self.vina_executable}")
            return False
        
        # 构建 Vina 命令
        cmd = [
            self.vina_executable,
            "--receptor", str(self.receptor_file),
            "--ligand", str(self.ligand_file),
            "--out", str(self.output_file),
            "--center_x", str(self.config['center_x']),
            "--center_y", str(self.config['center_y']),
            "--center_z", str(self.config['center_z']),
            "--size_x", str(self.config['size_x']),
            "--size_y", str(self.config['size_y']),
            "--size_z", str(self.config['size_z']),
            "--exhaustiveness", str(self.config['exhaustiveness']),
            "--num_modes", str(self.config['num_modes']),
            "--energy_range", str(self.config['energy_range'])
        ]
        
        logger.info("Running molecular docking...")
        logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            # 运行对接，设置超时时间为 10 分钟
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("Docking completed successfully!")
                logger.info(f"Results saved to: {self.output_file}")
                
                # 解析并显示结果
                self._parse_results()
                return True
            else:
                logger.error(f"Docking failed with return code: {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Docking timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"Error running docking: {e}")
            return False
    
    def _parse_results(self) -> List[Dict]:
        """解析并返回对接结果"""
        if not self.output_file.exists():
            return []
        
        try:
            with open(self.output_file, 'r') as f:
                content = f.read()
            
            # 提取结合能
            energies = []
            for line in content.split('\n'):
                if line.startswith('REMARK VINA RESULT:'):
                    parts = line.split()
                    if len(parts) >= 4:
                        energy = float(parts[3])
                        energies.append(energy)
            
            if energies:
                logger.info(f"\n=== Docking Results ===")
                for i, energy in enumerate(energies, 1):
                    logger.info(f"Model {i}: {energy:.3f} kcal/mol")
                
                best_energy = min(energies)
                logger.info(f"Best binding energy: {best_energy:.3f} kcal/mol")
            
            return energies
            
        except Exception as e:
            logger.warning(f"Could not parse results: {e}")
            return []


class PyMOLVisualizer:
    """PyMOL 可视化器 - 基于成熟的实现"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("pymol_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
        # 检查 PyMOL 是否可用
        self.pymol_available = False
        self.pymol = None
        self.cmd = None
        
        try:
            # 尝试多种PyMOL导入方式
            logger.info("🔍 检查PyMOL可用性...")
            
            # 方法1: 直接导入
            try:
                import pymol
                from pymol import cmd
                self.pymol_available = True
                self.pymol = pymol
                self.cmd = cmd
                logger.info("✅ PyMOL直接导入成功")
            except ImportError as e:
                logger.warning(f"⚠️ PyMOL直接导入失败: {e}")
                
                # 方法2: 尝试使用conda环境中的PyMOL
                try:
                    import sys
                    
                    # 检查是否有molecular-docking环境
                    current_project_root = Path(__file__).parent.parent.parent
                    conda_pymol_path = current_project_root / "docking_test" / "molecular-docking" / "lib" / "python3.11" / "site-packages"
                    
                    if conda_pymol_path.exists():
                        logger.info(f"🔍 尝试使用conda环境PyMOL: {conda_pymol_path}")
                        sys.path.insert(0, str(conda_pymol_path))
                        
                        import pymol
                        from pymol import cmd
                        self.pymol_available = True
                        self.pymol = pymol
                        self.cmd = cmd
                        logger.info("✅ Conda环境PyMOL导入成功")
                    else:
                        logger.warning("⚠️ 未找到conda环境PyMOL路径")
                        
                except Exception as e2:
                    logger.warning(f"⚠️ Conda环境PyMOL导入失败: {e2}")
                    
        except Exception as e:
            logger.error(f"❌ PyMOL检查过程出错: {e}")
            
        if not self.pymol_available:
            logger.warning("❌ PyMOL不可用。可视化将被跳过。")
            logger.info("💡 安装建议: conda install -c conda-forge pymol-open-source")
    
    def visualize_docking_results(self, protein_file: Path, ligand_file: Path, 
                                gui: bool = False, create_movie: bool = False) -> Dict[str, Any]:
        """
        生成分子对接可视化
        基于 docking_test/docking_visualization.py 的成熟实现
        """
        if not self.pymol_available:
            logger.error("PyMOL is not available")
            return {"success": False, "error": "PyMOL not available"}
        
        try:
            # 初始化 PyMOL - 添加超时和错误处理
            import threading
            
            def pymol_launcher():
                try:
                    if not gui:
                        # 设置环境变量确保无头模式
                        import os
                        os.environ['PYMOL_PATH'] = '/dev/null'
                        os.environ['DISPLAY'] = ''
                        # 无头模式，不显示 GUI
                        logger.info("启动PyMOL无头模式...")
                        self.pymol.finish_launching(['pymol', '-c', '-q'])  # 添加 -q 静默模式
                    else:
                        # GUI 模式
                        logger.info("启动PyMOL GUI模式...")
                        self.pymol.finish_launching()
                    logger.info("PyMOL启动成功")
                except Exception as e:
                    logger.error(f"PyMOL启动失败: {e}")
                    raise
            
            # 使用线程启动PyMOL，添加超时
            launch_thread = threading.Thread(target=pymol_launcher)
            launch_thread.daemon = True
            launch_thread.start()
            launch_thread.join(timeout=30)  # 30秒超时
            
            if launch_thread.is_alive():
                logger.error("PyMOL启动超时")
                return {"success": False, "error": "PyMOL launch timeout"}
            
            # 加载结构
            self._load_structures(protein_file, ligand_file)
            
            # 设置可视化样式
            self._setup_visualization()
            
            # 创建结合位点视图
            self._create_binding_site_view()
            
            # 生成多个视角的图像
            images = self._generate_images()
            
            # 保存会话
            session_file = self._save_session()
            
            # 创建动画（可选）
            if create_movie:
                self._create_movie()
            
            # 退出 PyMOL
            if not gui:
                self.cmd.quit()
            
            return {
                "success": True,
                "images": images,
                "session_file": str(session_file),
                "output_dir": str(self.output_dir)
            }
            
        except Exception as e:
            logger.error(f"Error in PyMOL visualization: {e}")
            if hasattr(self, 'cmd'):
                self.cmd.quit()
            return {"success": False, "error": str(e)}
    
    def _load_structures(self, protein_file: Path, ligand_file: Path):
        """加载蛋白质和配体结构"""
        logger.info(f"Loading receptor protein: {protein_file}")
        self.cmd.load(str(protein_file), "receptor")
        
        logger.info(f"Loading ligand molecule: {ligand_file}")
        self.cmd.load(str(ligand_file), "ligand")
        
        # 移除水分子和其他溶剂
        self.cmd.remove("solvent")
    
    def _setup_visualization(self):
        """设置可视化样式"""
        # 设置背景为白色
        self.cmd.bg_color("white")
        
        # 受体蛋白设置
        self.cmd.hide("everything", "receptor")
        self.cmd.show("cartoon", "receptor")
        self.cmd.show("surface", "receptor")
        self.cmd.set("surface_color", "gray80", "receptor")
        self.cmd.set("transparency", 0.7, "receptor")
        
        # 设置蛋白质卡通颜色
        self.cmd.color("slate", "receptor")
        
        # 配体设置
        self.cmd.hide("everything", "ligand")
        self.cmd.show("sticks", "ligand")
        self.cmd.show("spheres", "ligand")
        self.cmd.set("stick_radius", 0.15, "ligand")
        self.cmd.set("sphere_scale", 0.25, "ligand")
        
        # 配体着色
        self.cmd.color("orange", "ligand and elem C")
        self.cmd.color("blue", "ligand and elem N")
        self.cmd.color("red", "ligand and elem O")
        self.cmd.color("yellow", "ligand and elem S")
        self.cmd.color("white", "ligand and elem H")
    
    def _create_binding_site_view(self):
        """创建结合位点视图"""
        # 选择配体周围的残基
        self.cmd.select("binding_site", "receptor within 5 of ligand")
        
        # 显示结合位点的侧链
        self.cmd.show("sticks", "binding_site")
        self.cmd.show("lines", "binding_site")
        self.cmd.set("stick_radius", 0.1, "binding_site")
        
        # 着色结合位点
        self.cmd.color("cyan", "binding_site")
        
        # 创建氢键
        self.cmd.distance("hbonds", "ligand", "binding_site", 3.5, mode=2)
        self.cmd.hide("labels", "hbonds")
        self.cmd.color("yellow", "hbonds")
        self.cmd.set("dash_gap", 0.3, "hbonds")
        self.cmd.set("dash_length", 0.2, "hbonds")
    
    def _generate_images(self) -> List[str]:
        """生成多个视角的图像"""
        views = [
            ("overview", "全景视图", None),
            ("ligand_focus", "配体聚焦", "ligand"),
            ("binding_site", "结合位点", "binding_site or ligand"),
            ("surface_view", "表面视图", None),
            ("rotated_90", "旋转90度", None),
            ("top_view", "俯视图", None)
        ]
        
        images = []
        
        for view_name, description, selection in views:
            logger.info(f"Generating {description}...")
            
            if selection:
                self.cmd.zoom(selection, buffer=5)
            else:
                self.cmd.zoom("all", buffer=2)
            
            # 特定视角的调整
            if view_name == "rotated_90":
                self.cmd.rotate("y", 90)
            elif view_name == "top_view":
                self.cmd.rotate("x", 90)
            elif view_name == "surface_view":
                self.cmd.set("transparency", 0.3, "receptor")
                self.cmd.hide("cartoon", "receptor")
            
            # 光线追踪渲染（高质量）- 使用1920x1080分辨率和300 DPI
            output_file = self.output_dir / f"{view_name}.png"
            self.cmd.png(str(output_file), width=1920, height=1080, dpi=300, ray=1)
            images.append(str(output_file))
            
            # 恢复设置
            if view_name == "surface_view":
                self.cmd.set("transparency", 0.7, "receptor")
                self.cmd.show("cartoon", "receptor")
            
            # 重置视角
            if view_name in ["rotated_90", "top_view"]:
                self.cmd.orient()
        
        logger.info(f"All images saved to: {self.output_dir}")
        return images
    
    def _save_session(self) -> Path:
        """保存PyMOL会话文件"""
        session_file = self.output_dir / "docking_session.pse"
        self.cmd.save(str(session_file))
        logger.info(f"PyMOL session saved to: {session_file}")
        return session_file
    
    def _create_movie(self, frames: int = 360):
        """创建旋转动画"""
        logger.info("Generating rotation animation...")
        
        # 设置电影长度
        self.cmd.mset(f"1 x{frames}")
        
        # 创建旋转
        self.cmd.util.mroll(1, frames, 1)
        
        # 保存为单独的帧
        movie_dir = self.output_dir / "movie_frames"
        movie_dir.mkdir(exist_ok=True)
        
        for i in range(0, frames, 10):  # 每10帧保存一张
            self.cmd.frame(i + 1)
            frame_file = movie_dir / f"frame_{i:04d}.png"
            self.cmd.png(str(frame_file), width=800, height=600, ray=0)
        
        logger.info(f"Animation frames saved to: {movie_dir}")


class DockingAnalyzer:
    """对接结果分析器 - 基于成熟的科学分析实现"""
    
    def __init__(self, docking_results_file: Path):
        self.docking_file = docking_results_file
        self.binding_data = []
        self.models_data = []
    
    def analyze_docking_results(self, output_dir: Path = None) -> Dict[str, Any]:
        """
        分析对接结果并生成科学图表
        基于 docking_test/docking_analysis.py 的成熟实现
        """
        if output_dir is None:
            output_dir = self.docking_file.parent
        
        try:
            # 解析对接结果
            success = self._parse_docking_results()
            if not success:
                return {"success": False, "error": "Failed to parse docking results"}
            
            # 生成结合能图表
            binding_chart = self._generate_binding_energy_chart(output_dir)
            
            # 生成能量分解图表
            energy_chart = self._generate_energy_decomposition_chart(output_dir)
            
            # 生成科学报告
            report = self._generate_scientific_report(output_dir)
            
            return {
                "success": True,
                "models_count": len(self.models_data),
                "best_energy": min(d['binding_energy'] for d in self.models_data) if self.models_data else None,
                "binding_chart": str(binding_chart),
                "energy_chart": str(energy_chart),
                "report": str(report),
                "models_data": self.models_data
            }
            
        except Exception as e:
            logger.error(f"Error in docking analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_docking_results(self) -> bool:
        """解析对接结果文件"""
        logger.info(f"Analyzing docking results: {self.docking_file}")
        
        if not self.docking_file.exists():
            logger.error(f"Docking results file not found: {self.docking_file}")
            return False
        
        try:
            with open(self.docking_file, 'r') as f:
                content = f.read()
            
            # 提取模型数据
            import re
            models = re.findall(r'MODEL\s+(\d+)(.*?)ENDMDL', content, re.DOTALL)
            
            for model_num, model_content in models:
                model_data = self._parse_model(int(model_num), model_content)
                if model_data:
                    self.models_data.append(model_data)
            
            # 按结合能排序
            self.models_data.sort(key=lambda x: x['binding_energy'])
            
            logger.info(f"Successfully parsed {len(self.models_data)} docking models")
            return True
            
        except Exception as e:
            logger.error(f"Error parsing docking results: {e}")
            return False
    
    def _parse_model(self, model_num: int, model_content: str) -> Optional[Dict]:
        """解析单个模型的数据"""
        import re
        
        # 提取VINA结果行
        vina_match = re.search(r'REMARK VINA RESULT:\s*([-+]?\d*\.?\d+)\s*([-+]?\d*\.?\d+)\s*([-+]?\d*\.?\d+)', model_content)
        if not vina_match:
            return None
        
        binding_energy = float(vina_match.group(1))
        rmsd_lb = float(vina_match.group(2))
        rmsd_ub = float(vina_match.group(3))
        
        # 提取其他能量项
        inter_intra_match = re.search(r'REMARK INTER \+ INTRA:\s*([-+]?\d*\.?\d+)', model_content)
        inter_match = re.search(r'REMARK INTER:\s*([-+]?\d*\.?\d+)', model_content)
        intra_match = re.search(r'REMARK INTRA:\s*([-+]?\d*\.?\d+)', model_content)
        unbound_match = re.search(r'REMARK UNBOUND:\s*([-+]?\d*\.?\d+)', model_content)
        
        # 统计原子数量
        atom_lines = re.findall(r'^ATOM\s+\d+', model_content, re.MULTILINE)
        atom_count = len(atom_lines)
        
        # 统计可旋转键数量
        torsion_match = re.search(r'REMARK\s+(\d+)\s+active torsions:', model_content)
        active_torsions = int(torsion_match.group(1)) if torsion_match else 0
        
        return {
            'model': model_num,
            'binding_energy': binding_energy,
            'rmsd_lb': rmsd_lb,
            'rmsd_ub': rmsd_ub,
            'inter_intra': float(inter_intra_match.group(1)) if inter_intra_match else None,
            'inter': float(inter_match.group(1)) if inter_match else None,
            'intra': float(intra_match.group(1)) if intra_match else None,
            'unbound': float(unbound_match.group(1)) if unbound_match else None,
            'atom_count': atom_count,
            'active_torsions': active_torsions
        }
    
    def _generate_binding_energy_chart(self, output_dir: Path) -> Path:
        """生成结合能柱状图"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            if not self.models_data:
                raise ValueError("No model data available for analysis")
            
            # 设置样式
            plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
            plt.rcParams['axes.unicode_minus'] = False
            plt.style.use('default')
            
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            fig.suptitle('Molecular Docking Results Analysis', fontsize=16, fontweight='bold')
            
            # 子图1：结合能分析
            models = [data['model'] for data in self.models_data]
            energies = [data['binding_energy'] for data in self.models_data]
            
            # 使用渐变色彩
            colors = plt.cm.RdYlBu_r(np.linspace(0.2, 0.8, len(models)))
            bars1 = ax1.bar(models, energies, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
            
            ax1.set_xlabel('Docking Model', fontsize=12)
            ax1.set_ylabel('Binding Energy (kcal/mol)', fontsize=12)
            ax1.set_title('Binding Energy by Docking Model', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # 添加数值标签
            for bar, energy in zip(bars1, energies):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                        f'{energy:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            # 高亮最佳结合能
            if energies:
                best_idx = energies.index(min(energies))
                bars1[best_idx].set_color('#FF6B6B')
                bars1[best_idx].set_alpha(1.0)
                bars1[best_idx].set_linewidth(2)
            
            # 子图2：RMSD分析
            rmsd_lb = [data['rmsd_lb'] for data in self.models_data]
            rmsd_ub = [data['rmsd_ub'] for data in self.models_data]
            
            x_pos = np.arange(len(models))
            width = 0.35
            
            ax2.bar(x_pos - width/2, rmsd_lb, width, label='RMSD Lower Bound', 
                   color='#4ECDC4', alpha=0.8, edgecolor='black', linewidth=0.5)
            ax2.bar(x_pos + width/2, rmsd_ub, width, label='RMSD Upper Bound', 
                   color='#45B7D1', alpha=0.8, edgecolor='black', linewidth=0.5)
            
            ax2.set_xlabel('Docking Model', fontsize=12)
            ax2.set_ylabel('RMSD (Å)', fontsize=12)
            ax2.set_title('Root Mean Square Deviation Analysis', fontsize=14, fontweight='bold')
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels(models)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            output_file = output_dir / "binding_energies.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Binding energy chart saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error generating binding energy chart: {e}")
            raise
    
    def _generate_energy_decomposition_chart(self, output_dir: Path) -> Path:
        """生成能量分解图表"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # 创建能量分解图表
            fig, ax = plt.subplots(figsize=(10, 6))
            
            models = [data['model'] for data in self.models_data if data.get('inter')]
            if not models:
                # 如果没有能量分解数据，创建简单的能量对比图
                models = [data['model'] for data in self.models_data]
                energies = [data['binding_energy'] for data in self.models_data]
                
                ax.plot(models, energies, 'o-', linewidth=2, markersize=8, color='#FF6B6B')
                ax.set_title('Binding Energy Trend', fontsize=14, fontweight='bold')
                ax.set_ylabel('Binding Energy (kcal/mol)', fontsize=12)
            else:
                # 绘制能量分解
                inter_energies = [data.get('inter', 0) for data in self.models_data if data.get('inter')]
                intra_energies = [data.get('intra', 0) for data in self.models_data if data.get('intra')]
                
                ax.plot(models, inter_energies, 'o-', label='Intermolecular', linewidth=2, markersize=6)
                ax.plot(models, intra_energies, 's-', label='Intramolecular', linewidth=2, markersize=6)
                ax.legend()
                ax.set_title('Energy Decomposition Analysis', fontsize=14, fontweight='bold')
                ax.set_ylabel('Energy (kcal/mol)', fontsize=12)
            
            ax.set_xlabel('Docking Model', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            output_file = output_dir / "energy_decomposition.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Energy decomposition chart saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error generating energy decomposition chart: {e}")
            raise
    
    def _generate_scientific_report(self, output_dir: Path) -> Path:
        """生成科学分析报告"""
        try:
            if not self.models_data:
                raise ValueError("No model data available for report")
            
            best_model = self.models_data[0]  # 已按能量排序
            energies = [data['binding_energy'] for data in self.models_data]
            
            # 计算统计数据
            mean_energy = sum(energies) / len(energies)
            std_energy = (sum((e - mean_energy) ** 2 for e in energies) / len(energies)) ** 0.5
            
            # 估算 Ki 值 (经验公式: Ki ≈ exp(ΔG/RT), RT ≈ 0.592 kcal/mol at 298K)
            best_ki = None
            best_ki_um = None
            if best_model['binding_energy'] < 0:
                RT = 0.592  # kcal/mol at 298K
                best_ki = 1e9 * (2.718281828 ** (best_model['binding_energy'] / RT))  # nM
                best_ki_um = best_ki / 1000  # μM
            
            # 生成报告内容
            report_content = f"""
# Molecular Docking Analysis Report

## Summary
- **Total Models**: {len(self.models_data)}
- **Best Binding Energy**: {best_model['binding_energy']:.3f} kcal/mol (Model {best_model['model']})
- **Mean Binding Energy**: {mean_energy:.3f} ± {std_energy:.3f} kcal/mol
- **RMSD Range**: {best_model['rmsd_lb']:.2f} - {best_model['rmsd_ub']:.2f} Å

## Best Model Details (Model {best_model['model']})
- **Binding Affinity**: {best_model['binding_energy']:.3f} kcal/mol
- **Estimated Ki**: {f"{best_ki:.2e} nM ({best_ki_um:.2f} μM)" if best_ki is not None else "N/A (positive binding energy)"}
- **RMSD Lower Bound**: {best_model['rmsd_lb']:.2f} Å
- **RMSD Upper Bound**: {best_model['rmsd_ub']:.2f} Å
- **Atom Count**: {best_model.get('atom_count', 'N/A')}
- **Active Torsions**: {best_model.get('active_torsions', 'N/A')}

## Binding Affinity Interpretation
"""
            
            # 添加结合强度解释
            if best_model['binding_energy'] < -10.0:
                report_content += "- **Excellent**: Very strong binding affinity (< -10.0 kcal/mol)\n"
            elif best_model['binding_energy'] < -8.0:
                report_content += "- **Very Good**: Strong binding affinity (-10.0 to -8.0 kcal/mol)\n"
            elif best_model['binding_energy'] < -6.0:
                report_content += "- **Good**: Moderate binding affinity (-8.0 to -6.0 kcal/mol)\n"
            elif best_model['binding_energy'] < -4.0:
                report_content += "- **Weak**: Weak binding affinity (-6.0 to -4.0 kcal/mol)\n"
            else:
                report_content += "- **Very Weak**: Very weak binding affinity (> -4.0 kcal/mol)\n"
            
            # 添加所有模型的详细数据
            report_content += "\n## All Models Data\n\n"
            report_content += "| Model | Binding Energy (kcal/mol) | RMSD LB (Å) | RMSD UB (Å) |\n"
            report_content += "|-------|---------------------------|--------------|-------------|\n"
            
            for data in self.models_data:
                report_content += f"| {data['model']} | {data['binding_energy']:.3f} | {data['rmsd_lb']:.2f} | {data['rmsd_ub']:.2f} |\n"
            
            report_content += f"\n## Analysis Date\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # 保存报告
            output_file = output_dir / "docking_analysis_report.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Scientific report saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error generating scientific report: {e}")
            raise


class DockingEngine:
    """
    集成分子对接引擎
    整合蛋白质预处理、分子对接、PyMOL可视化和科学分析
    """
    
    def __init__(self):
        self.preprocessor = ProteinPreprocessor()
        self.docker = MolecularDocker()
        self.visualizer = PyMOLVisualizer()
        self.analyzer = None  # 将在对接完成后初始化
    
    def run_complete_docking_pipeline(self, 
                                    protein_path: Path, 
                                    ligand_smiles: str,
                                    pocket_center: List[float],
                                    box_size: List[float] = None,
                                    output_dir: Path = None,
                                    ligand_pdbqt_path: Path = None) -> Dict[str, Any]:
        """
        运行完整的分子对接流程
        
        Args:
            protein_path: 蛋白质PDB文件路径
            ligand_smiles: 配体SMILES字符串
            pocket_center: 对接口袋中心坐标 [x, y, z]
            box_size: 搜索盒子大小 [x, y, z]，默认 [20, 20, 20]
            output_dir: 输出目录，默认基于蛋白质文件名创建
            ligand_pdbqt_path: 预生成的配体PDBQT文件路径（可选）
            
        Returns:
            包含所有结果的字典
        """
        try:
            logger.info("🌟" * 30)
            logger.info("🚀 DockingEngine.run_complete_docking_pipeline 开始")
            logger.info(f"📁 蛋白质路径: {protein_path}")
            logger.info(f"🧬 配体SMILES: {ligand_smiles[:30]}...")
            logger.info(f"📍 口袋中心: {pocket_center}")
            logger.info(f"📦 盒子大小: {box_size}")
            logger.info(f"📂 输出目录: {output_dir}")
            logger.info(f"💊 预生成配体: {ligand_pdbqt_path}")
            
            # 设置默认参数
            if box_size is None:
                box_size = [20.0, 20.0, 20.0]
                logger.info(f"📦 使用默认盒子大小: {box_size}")
            
            if output_dir is None:
                # 默认使用项目根目录下的temp目录
                project_root = Path(__file__).parent.parent.parent
                temp_base = project_root / "temp"
                temp_base.mkdir(exist_ok=True)
                
                import time
                timestamp = int(time.time())
                output_dir = temp_base / f"docking_{timestamp}"
                logger.info(f"📂 使用默认输出目录: {output_dir}")
            else:
                logger.info(f"📂 使用指定输出目录: {output_dir}")
            
            logger.info(f"📁 创建输出目录: {output_dir}")
            output_dir.mkdir(exist_ok=True)
            logger.info("✅ 输出目录创建成功")
            
            # 步骤1: 准备蛋白质结构
            logger.info("🔧 步骤1: 准备蛋白质结构...")
            target_receptor_file = output_dir / "protein_receptor.pdbqt"
            logger.info(f"🎯 目标受体文件: {target_receptor_file}")
            
            receptor_file = self.preprocessor.fix_protein_structure(
                protein_path, 
                target_receptor_file
            )
            
            logger.info(f"📋 受体文件处理结果: {receptor_file}")
            
            if not receptor_file:
                logger.error("❌ 蛋白质结构准备失败")
                raise ProcessingError("Failed to prepare protein structure")
            
            logger.info("✅ 步骤1完成: 蛋白质结构准备成功")
            
            # 步骤2: 准备配体结构
            logger.info("💊 步骤2: 准备配体结构...")
            ligand_file = output_dir / "ligand.pdbqt"
            logger.info(f"🎯 目标配体文件: {ligand_file}")
            
            if ligand_pdbqt_path and ligand_pdbqt_path.exists():
                # 使用预生成的配体文件
                import shutil
                logger.info(f"📋 复制预生成配体文件: {ligand_pdbqt_path} -> {ligand_file}")
                shutil.copy2(ligand_pdbqt_path, ligand_file)
                logger.info("✅ 预生成配体文件复制成功")
            else:
                # 需要生成配体文件，这里先创建一个占位符
                logger.warning("⚠️ 配体PDBQT文件未提供 - 可能导致对接失败")
                logger.info("📝 创建配体占位符文件...")
                # 创建一个简单的占位符文件，实际使用中应该有有效的配体文件
                with open(ligand_file, 'w') as f:
                    f.write("REMARK Placeholder ligand file\n")
                    f.write("REMARK SMILES: " + ligand_smiles + "\n")
                logger.info("✅ 配体占位符文件创建完成")
            
            logger.info("✅ 步骤2完成: 配体结构准备成功")
            
            # 步骤3: 设置并运行分子对接
            logger.info("⚔️ 步骤3: 运行分子对接...")
            logger.info(f"🔧 设置对接器文件:")
            logger.info(f"   - 受体: {receptor_file}")
            logger.info(f"   - 配体: {ligand_file}")
            logger.info(f"   - 输出目录: {output_dir}")
            logger.info("⚙️ 设置对接器参数...")
            output_docking_file = output_dir / "docking_results.pdbqt"
            logger.info(f"📤 对接结果文件: {output_docking_file}")
            
            self.docker.set_files(
                receptor_file, 
                ligand_file,
                output_docking_file
            )
            
            logger.info(f"🎯 设置搜索空间:")
            logger.info(f"   - 中心: ({pocket_center[0]}, {pocket_center[1]}, {pocket_center[2]})")
            logger.info(f"   - 大小: ({box_size[0]}, {box_size[1]}, {box_size[2]})")
            
            self.docker.set_search_space(
                pocket_center[0], pocket_center[1], pocket_center[2],
                box_size[0], box_size[1], box_size[2]
            )
            
            logger.info("🚀 开始执行Vina分子对接...")
            docking_success = self.docker.run_docking()
            logger.info(f"⚡ Vina对接完成，结果: {'成功' if docking_success else '失败'}")
            
            if not docking_success:
                logger.error("❌ 分子对接执行失败")
                raise ProcessingError("Molecular docking failed")
                
            logger.info("✅ 步骤3完成: 分子对接成功")
            
            # 步骤4: 生成PyMOL可视化（使用原始经过验证的实现）
            logger.info("Step 4: Generating PyMOL visualizations...")
            try:
                # 使用原始docking_test中经过验证的可视化函数
                from pathlib import Path
                import sys
                
                # 获取项目根目录
                current_project_root = Path(__file__).parent.parent.parent
                
                # 添加docking_test路径
                docking_test_path = current_project_root / "docking_test"
                if str(docking_test_path) not in sys.path:
                    sys.path.insert(0, str(docking_test_path))
                
                # 导入原始可视化函数
                from docking_visualization import visualize_docking_results
                
                logger.info(f"🎨 调用原始可视化函数...")
                logger.info(f"   - protein_file: {receptor_file}")
                logger.info(f"   - ligand_file: {self.docker.output_file}")
                logger.info(f"   - output_dir: {output_dir}")
                
                # 调用原始的经过验证的可视化函数
                visualization_success = visualize_docking_results(
                    protein_file=str(receptor_file),
                    ligand_file=str(self.docker.output_file),
                    output_dir=str(output_dir),
                    use_pymol=True,
                    use_web=True,
                    interactive_pymol=False,
                    create_movie=False
                )
                
                if visualization_success:
                    logger.info("✅ 原始可视化函数执行成功")
                    visualization_result = {
                        "success": True,
                        "output_dir": str(output_dir),
                        "method": "original_docking_test_visualization"
                    }
                else:
                    logger.warning("⚠️ 原始可视化函数报告失败，但继续执行")
                    visualization_result = {
                        "success": False,
                        "error": "Original visualization function returned False",
                        "output_dir": str(output_dir),
                        "method": "original_docking_test_visualization"
                    }
                
                # 从sys.path移除docking_test路径（可选）
                if str(docking_test_path) in sys.path:
                    sys.path.remove(str(docking_test_path))
                    
            except Exception as e:
                logger.error(f"❌ 原始可视化函数执行失败: {e}")
                logger.info("🔄 降级到内置可视化器...")
                
                # 降级到内置可视化器
                self.visualizer = PyMOLVisualizer(output_dir)
                visualization_result = self.visualizer.visualize_docking_results(
                    receptor_file, 
                    self.docker.output_file,
                    gui=False,
                    create_movie=False
                )
            
            # 步骤5: 进行科学分析
            logger.info("Step 5: Performing scientific analysis...")
            
            # 确保使用正确的对接结果文件
            docking_result_file = self.docker.output_file
            if not docking_result_file.exists():
                # 尝试查找其他可能的结果文件
                possible_files = [
                    output_dir / "docking_results.pdbqt",
                    output_dir / "docking_result.pdbqt",
                    protein_path.parent / "docking_result.pdbqt"
                ]
                for possible_file in possible_files:
                    if possible_file.exists():
                        logger.info(f"Using alternative docking result file: {possible_file}")
                        docking_result_file = possible_file
                        break
            
            self.analyzer = DockingAnalyzer(docking_result_file)
            analysis_result = self.analyzer.analyze_docking_results(output_dir)
            
            # 编译最终结果
            final_result = {
                "success": True,
                "output_dir": str(output_dir),
                "receptor_file": str(receptor_file),
                "ligand_file": str(ligand_file),
                "docking_file": str(self.docker.output_file),
                "ligand_smiles": ligand_smiles,
                "pocket_center": pocket_center,
                "box_size": box_size,
                "timestamp": datetime.now().isoformat(),
                "visualization": visualization_result,
                "analysis": analysis_result
            }
            
            # 添加最佳对接评分
            if analysis_result.get("success") and analysis_result.get("best_energy"):
                final_result["best_score"] = analysis_result["best_energy"]
                final_result["models_count"] = analysis_result.get("models_count", 0)
                
                # 创建构象列表（兼容现有API）
                poses = []
                if analysis_result.get("models_data"):
                    poses = [
                        {
                            "pose_id": model["model"],
                            "binding_affinity": model["binding_energy"],
                            "rmsd_lower": model.get("rmsd_lb", 0.0),
                            "rmsd_upper": model.get("rmsd_ub", 0.0)
                        }
                        for model in analysis_result["models_data"]
                    ]
                final_result["poses"] = poses
                final_result["num_poses"] = len(poses)  # 添加 num_poses 字段
            
            logger.info("Complete docking pipeline finished successfully!")
            return final_result
            
        except Exception as e:
            logger.error(f"Docking pipeline failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ligand_smiles": ligand_smiles,
                "protein_path": str(protein_path),
                "pocket_center": pocket_center
            }