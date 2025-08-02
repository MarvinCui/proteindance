"""
可视化引擎 - 处理分子结构可视化和图像生成
"""
import base64
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from io import BytesIO

from ..core.config import settings
from ..models.exceptions import ProcessingError
from ..utils.display import print_info, print_error, print_subsection, Colors

logger = logging.getLogger(__name__)

# 可选导入
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Draw, Descriptors, Lipinski, rdMolDescriptors
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

try:
    import py3Dmol
    HAS_PY3DMOL = True
except ImportError:
    HAS_PY3DMOL = False

try:
    from .visualizers.docking_visualizer import DockingVisualizer, WebVisualizer
    HAS_PYMOL = True
except ImportError:
    HAS_PYMOL = False


class VisualizationEngine:
    """可视化引擎类 - 负责分子结构可视化"""
    
    def __init__(self):
        """初始化可视化引擎"""
        if not HAS_RDKIT:
            logger.warning("RDKit未安装，分子可视化功能受限")
    
    def generate_molecule_image(self, smiles: str, output_path: Optional[Path] = None, 
                               size: tuple = (600, 400)) -> Optional[str]:
        """
        生成分子的2D结构图像
        
        Args:
            smiles: SMILES字符串
            output_path: 输出路径
            size: 图像尺寸
        
        Returns:
            图像文件路径，失败返回None
        """
        try:
            if not HAS_RDKIT:
                raise ProcessingError("RDKit未安装，无法生成分子图像")
            
            print_info("正在生成分子结构图...")
            
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                raise ProcessingError(f"无法从SMILES生成分子: {smiles}")
            
            # 添加氢原子和2D坐标
            mol = Chem.AddHs(mol)
            AllChem.Compute2DCoords(mol)
            
            # 生成图像
            img = Draw.MolToImage(mol, size=size, kekulize=True)
            
            # 保存图像
            if output_path is None:
                output_path = settings.TMP_DIR / f"molecule_{int(time.time())}.png"
            
            img.save(output_path)
            logger.info(f"分子图像已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"生成分子结构图失败: {str(e)}")
            print_error(f"生成分子结构图失败: {str(e)}")
            return None

    def molecule_to_base64(self, smiles: str, size: tuple = (600, 400)) -> Optional[str]:
        """
        将分子转换为base64编码的图像
        
        Args:
            smiles: SMILES字符串
            size: 图像尺寸
        
        Returns:
            base64编码的图像数据，失败返回None
        """
        try:
            if not HAS_RDKIT:
                raise ProcessingError("RDKit未安装，无法生成分子图像")
            
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                raise ProcessingError(f"无法从SMILES生成分子: {smiles}")
            
            # 添加氢原子和2D坐标
            mol = Chem.AddHs(mol)
            AllChem.Compute2DCoords(mol)
            
            # 生成图像
            img = Draw.MolToImage(mol, size=size, kekulize=True)
            
            # 转换为base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return img_data
            
        except Exception as e:
            logger.error(f"生成分子base64图像失败: {str(e)}")
            return None
    
    def display_molecule_ascii(self, smiles: str) -> None:
        """
        在终端中显示分子的文本信息
        
        Args:
            smiles: SMILES字符串
        """
        try:
            if not HAS_RDKIT:
                print_error("RDKit未安装，无法显示分子信息")
                return
            
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                print_error(f"无法从SMILES生成分子: {smiles}")
                return
            
            # 显示分子基本信息
            print_subsection("分子基本信息")
            print(f"{Colors.OKBLUE}分子式:{Colors.ENDC} {rdMolDescriptors.CalcMolFormula(mol)}")
            print(f"{Colors.OKBLUE}分子量:{Colors.ENDC} {round(Descriptors.MolWt(mol), 2)}")
            print(f"{Colors.OKBLUE}氢键受体:{Colors.ENDC} {Lipinski.NumHAcceptors(mol)}")
            print(f"{Colors.OKBLUE}氢键供体:{Colors.ENDC} {Lipinski.NumHDonors(mol)}")
            print(f"{Colors.OKBLUE}旋转键:{Colors.ENDC} {Lipinski.NumRotatableBonds(mol)}")
            print(f"{Colors.OKBLUE}LogP:{Colors.ENDC} {round(Descriptors.MolLogP(mol), 2)}")
            print(f"{Colors.OKBLUE}TPSA:{Colors.ENDC} {round(Descriptors.TPSA(mol), 2)}")
            
            # Lipinski规则检查
            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            hbd = Lipinski.NumHDonors(mol)
            hba = Lipinski.NumHAcceptors(mol)
            
            lipinski_violations = 0
            if mw > 500:
                lipinski_violations += 1
            if logp > 5:
                lipinski_violations += 1
            if hbd > 5:
                lipinski_violations += 1
            if hba > 10:
                lipinski_violations += 1
            
            print(f"{Colors.OKBLUE}Lipinski规则违反:{Colors.ENDC} {lipinski_violations}/4")
            if lipinski_violations <= 1:
                print(f"{Colors.OKGREEN}✓ 符合药物样性质{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ 可能不符合药物样性质{Colors.ENDC}")
            
        except Exception as e:
            logger.error(f"显示分子信息失败: {str(e)}")
            print_error(f"显示分子信息失败: {str(e)}")
    
    def generate_3d_viewer(self, smiles: Optional[str] = None, pdb_data: Optional[str] = None) -> Optional[str]:
        """
        生成3D分子查看器HTML
        
        Args:
            smiles: SMILES字符串（可选）
            pdb_data: PDB数据（可选）
        
        Returns:
            HTML字符串，失败返回None
        """
        try:
            if not HAS_PY3DMOL:
                logger.warning("py3Dmol未安装，无法生成3D查看器")
                return None
            
            # 创建3D查看器
            viewer = py3Dmol.view(width=800, height=600)
            
            # 添加小分子（如果提供）
            if smiles:
                if not HAS_RDKIT:
                    logger.warning("RDKit未安装，无法生成3D结构")
                    return None
                
                # 生成3D结构
                mol = Chem.MolFromSmiles(smiles)
                if not mol:
                    raise ProcessingError(f"无法从SMILES生成分子: {smiles}")
                
                mol = Chem.AddHs(mol)
                AllChem.EmbedMolecule(mol, AllChem.ETKDG())
                AllChem.UFFOptimizeMolecule(mol)
                
                # 转换为SDF格式
                sdf_data = Chem.MolToMolBlock(mol)
                viewer.addModel(sdf_data, 'sdf')
                viewer.setStyle({'stick': {}})
            
            # 添加蛋白质（如果提供）
            if pdb_data:
                viewer.addModel(pdb_data, 'pdb')
                model_index = 1 if smiles else 0
                viewer.setStyle({'model': model_index}, {'cartoon': {'color': 'spectrum'}})
            
            viewer.zoomTo()
            return viewer._make_html()
            
        except Exception as e:
            logger.error(f"生成3D查看器失败: {str(e)}")
            return None
    
    def create_docking_visualization(self, protein_pdb: str, ligand_smiles: str, 
                                   pocket_center: tuple) -> Optional[str]:
        """
        创建蛋白质-配体对接可视化
        
        Args:
            protein_pdb: 蛋白质PDB数据
            ligand_smiles: 配体SMILES
            pocket_center: 口袋中心坐标
        
        Returns:
            HTML可视化字符串，失败返回None
        """
        try:
            if not HAS_PY3DMOL or not HAS_RDKIT:
                logger.warning("缺少必要的可视化库")
                return None
            
            # 生成配体3D结构
            mol = Chem.MolFromSmiles(ligand_smiles)
            if not mol:
                return None
            
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, AllChem.ETKDG())
            AllChem.UFFOptimizeMolecule(mol)
            
            # 将配体移动到口袋中心附近
            conf = mol.GetConformer()
            for i in range(mol.GetNumAtoms()):
                pos = conf.GetAtomPosition(i)
                conf.SetAtomPosition(i, (
                    pos.x + pocket_center[0],
                    pos.y + pocket_center[1], 
                    pos.z + pocket_center[2]
                ))
            
            ligand_sdf = Chem.MolToMolBlock(mol)
            
            # 创建可视化
            viewer = py3Dmol.view(width=800, height=600)
            
            # 添加蛋白质
            viewer.addModel(protein_pdb, 'pdb')
            viewer.setStyle({'model': 0}, {'cartoon': {'color': 'spectrum'}})
            
            # 添加配体
            viewer.addModel(ligand_sdf, 'sdf')
            viewer.setStyle({'model': 1}, {'stick': {'colorscheme': 'greenCarbon'}})
            
            # 添加口袋球体
            viewer.addSphere({
                'center': {'x': pocket_center[0], 'y': pocket_center[1], 'z': pocket_center[2]},
                'radius': 5.0,
                'color': 'red',
                'alpha': 0.3
            })
            
            viewer.zoomTo()
            return viewer._make_html()
            
        except Exception as e:
            logger.error(f"创建对接可视化失败: {str(e)}")
            return None
    
    def generate_docking_visualization(self, protein_file: str, ligand_file: str, output_dir: str, 
                                     use_pymol: bool = True, use_web: bool = True, 
                                     interactive_pymol: bool = False, create_movie: bool = False) -> Dict[str, Any]:
        """
        生成对接结果的可视化
        
        Args:
            protein_file: 蛋白质文件路径
            ligand_file: 配体文件路径
            output_dir: 输出目录
            use_pymol: 是否使用PyMOL生成图像
            use_web: 是否生成3Dmol.js网页
            interactive_pymol: 是否以交互模式运行PyMOL
            create_movie: 是否生成动画
            
        Returns:
            一个包含可视化结果路径的字典
        """
        if not HAS_PYMOL:
            raise ProcessingError("PyMOL或其依赖项未安装，无法进行对接可视化")
            
        results = {
            "status": "success",
            "pymol_images": [],
            "web_viewer": None,
            "session_file": None,
            "movie_dir": None
        }
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print_subsection("开始生成对接可视化...")
        
        try:
            # PyMOL 可视化
            if use_pymol:
                print_info("1. 生成PyMOL图像...")
                visualizer = DockingVisualizer(
                    receptor_file=protein_file,
                    ligand_file=ligand_file,
                    output_dir=str(output_path),
                    gui=interactive_pymol
                )
                success = visualizer.run(create_movie=create_movie)
                if not success:
                    results["status"] = "partial_failure"
                    results["error_pymol"] = "PyMOL visualization failed"
                else:
                    # 收集生成的图像
                    for f in output_path.glob("*.png"):
                        results["pymol_images"].append(str(f))
                    
                    session_file = output_path / "docking_session.pse"
                    if session_file.exists():
                        results["session_file"] = str(session_file)
                    
                    if create_movie:
                        movie_dir = output_path / "movie_frames"
                        if movie_dir.exists():
                            results["movie_dir"] = str(movie_dir)

            # Web 可视化
            if use_web:
                print_info("2. 生成Web可视化...")
                web_viz = WebVisualizer()
                web_viz.set_files(protein_file, ligand_file, str(output_path))
                web_viewer_path = web_viz.generate_web_viewer()
                results["web_viewer"] = str(web_viewer_path)

        except Exception as e:
            logger.error(f"对接可视化失败: {e}", exc_info=True)
            print_error(f"对接可视化失败: {e}")
            results["status"] = "failure"
            results["error"] = str(e)

        print_info("对接可视化完成。")
        return results
    
    def generate_docking_image(self, protein_pdb_path: str, ligand_smiles: str, 
                              pocket_center: list, box_size: list = None) -> Dict[str, Any]:
        """
        生成分子对接静态图像
        基于 docking_test/docking_visualization.py 的成熟实现
        
        Args:
            protein_pdb_path: 蛋白质PDB文件路径
            ligand_smiles: 配体SMILES字符串
            pocket_center: 口袋中心坐标 [x, y, z]
            box_size: 搜索盒子大小 [x, y, z]
            
        Returns:
            包含图像路径的字典
        """
        try:
            logger.info(f"开始生成对接图像: {protein_pdb_path}")
            logger.info(f"配体SMILES长度: {len(ligand_smiles)} 字符")
            
            # 检查配体分子复杂度
            if len(ligand_smiles) > 150:
                logger.warning(f"配体分子过于复杂 ({len(ligand_smiles)} 字符)，跳过图像生成以避免超时")
                return {
                    "success": False,
                    "error": "Ligand molecule too complex for visualization",
                    "message": f"Ligand SMILES ({len(ligand_smiles)} chars) exceeds complexity limit",
                    "pocket_center": pocket_center,
                    "ligand_smiles": ligand_smiles[:50] + "..." if len(ligand_smiles) > 50 else ligand_smiles
                }
            
            # 先尝试使用PyMOL可视化（如果PyMOL可用）
            try:
                import pymol
                from pymol import cmd
                pymol_available = True
            except ImportError:
                pymol_available = False
                logger.warning("PyMOL不可用，将使用替代方案")
            
            if pymol_available:
                return self._generate_pymol_docking_image(
                    protein_pdb_path, ligand_smiles, pocket_center, box_size
                )
            else:
                # 如果PyMOL不可用，返回基础响应
                return {
                    "success": False,
                    "error": "PyMOL not available for high-quality visualization",
                    "fallback_message": "Using alternative visualization methods",
                    "pocket_center": pocket_center,
                    "ligand_smiles": ligand_smiles
                }
                
        except Exception as e:
            logger.error(f"对接图像生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "pocket_center": pocket_center,
                "ligand_smiles": ligand_smiles
            }
    
    def _generate_pymol_docking_image(self, protein_pdb_path: str, ligand_smiles: str,
                                     pocket_center: list, box_size: list = None) -> Dict[str, Any]:
        """
        使用PyMOL生成对接图像
        基于docking_test中的成熟PyMOL可视化代码
        """
        try:
            import pymol
            from pymol import cmd
            import tempfile
            from pathlib import Path
            
            # 创建临时输出目录
            output_dir = Path(settings.TMP_DIR) / "docking_images"
            output_dir.mkdir(exist_ok=True)
            
            # 初始化PyMOL（无头模式）- 添加超时保护
            import threading
            
            def pymol_launcher():
                try:
                    # 设置环境变量确保无头模式
                    import os
                    os.environ['PYMOL_PATH'] = '/dev/null'
                    os.environ['DISPLAY'] = ''
                    logger.info("启动PyMOL无头模式进行图像生成...")
                    pymol.finish_launching(['pymol', '-c', '-q'])  # 添加 -q 静默模式
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
                return {
                    "success": False,
                    "error": "PyMOL launch timeout",
                    "pocket_center": pocket_center,
                    "ligand_smiles": ligand_smiles
                }
            
            # 设置背景为白色
            cmd.bg_color("white")
            
            # 加载蛋白质结构
            logger.info(f"加载蛋白质结构: {protein_pdb_path}")
            cmd.load(protein_pdb_path, "protein")
            
            # 移除水分子和其他溶剂
            cmd.remove("solvent")
            
            # 设置蛋白质可视化样式
            cmd.hide("everything", "protein")
            cmd.show("cartoon", "protein")
            cmd.show("surface", "protein")
            cmd.set("surface_color", "gray80", "protein")
            cmd.set("transparency", 0.7, "protein")
            cmd.color("slate", "protein")
            
            # 如果有口袋中心，创建口袋标记
            if pocket_center and len(pocket_center) >= 3:
                logger.info(f"标记结合口袋位置: {pocket_center}")
                
                # 创建伪原子标记口袋中心
                cmd.pseudoatom("pocket_center", 
                              pos=[pocket_center[0], pocket_center[1], pocket_center[2]])
                cmd.show("spheres", "pocket_center")
                cmd.color("red", "pocket_center")
                cmd.set("sphere_scale", 2.0, "pocket_center")
                
                # 选择口袋周围的残基
                cmd.select("pocket_residues", 
                          f"protein within 8 of pocket_center")
                
                # 显示口袋残基
                cmd.show("sticks", "pocket_residues")
                cmd.color("cyan", "pocket_residues")
                cmd.set("stick_radius", 0.15, "pocket_residues")
                
                # 如果有盒子大小，显示搜索空间
                if box_size and len(box_size) >= 3:
                    # 创建盒子边界的伪原子
                    half_x, half_y, half_z = box_size[0]/2, box_size[1]/2, box_size[2]/2
                    cx, cy, cz = pocket_center[0], pocket_center[1], pocket_center[2]
                    
                    # 创建盒子的8个角点
                    corners = [
                        [cx-half_x, cy-half_y, cz-half_z],
                        [cx+half_x, cy-half_y, cz-half_z],
                        [cx-half_x, cy+half_y, cz-half_z],
                        [cx+half_x, cy+half_y, cz-half_z],
                        [cx-half_x, cy-half_y, cz+half_z],
                        [cx+half_x, cy-half_y, cz+half_z],
                        [cx-half_x, cy+half_y, cz+half_z],
                        [cx+half_x, cy+half_y, cz+half_z]
                    ]
                    
                    for i, corner in enumerate(corners):
                        cmd.pseudoatom(f"box_corner_{i}", pos=corner)
                    
                    cmd.show("spheres", "box_corner_*")
                    cmd.color("yellow", "box_corner_*")
                    cmd.set("sphere_scale", 0.5, "box_corner_*")
            
            # 生成多个视角的图像
            images = []
            views = [
                ("overview", "全景视图", "all"),
                ("pocket_focus", "口袋聚焦", "pocket_center" if pocket_center else "protein"),
                ("protein_surface", "蛋白质表面", "protein")
            ]
            
            for view_name, description, selection in views:
                logger.info(f"生成{description}...")
                
                # 设置视角
                if selection == "all":
                    cmd.zoom("all", buffer=2)
                elif selection.startswith("pocket"):
                    if pocket_center:
                        cmd.zoom("pocket_center", buffer=10)
                    else:
                        cmd.zoom("protein", buffer=5)
                else:
                    cmd.zoom(selection, buffer=5)
                
                # 为pocket_focus调整表面透明度
                if view_name == "pocket_focus":
                    cmd.set("transparency", 0.5, "protein")
                
                # 渲染高质量图像
                output_file = output_dir / f"{view_name}.png"
                cmd.png(str(output_file), width=1200, height=900, dpi=150, ray=1)
                images.append(str(output_file))
                
                # 恢复透明度
                if view_name == "pocket_focus":
                    cmd.set("transparency", 0.7, "protein")
            
            # 退出PyMOL
            cmd.quit()
            
            logger.info(f"成功生成 {len(images)} 张对接图像")
            
            return {
                "success": True,
                "images": images,
                "output_dir": str(output_dir),
                "pocket_center": pocket_center,
                "ligand_smiles": ligand_smiles,
                "message": f"Generated {len(images)} docking visualization images"
            }
            
        except Exception as e:
            logger.error(f"PyMOL对接图像生成失败: {e}")
            # 确保PyMOL退出
            try:
                from pymol import cmd
                cmd.quit()
            except:
                pass
            
            return {
                "success": False,
                "error": f"PyMOL visualization failed: {str(e)}",
                "pocket_center": pocket_center,
                "ligand_smiles": ligand_smiles
            }
