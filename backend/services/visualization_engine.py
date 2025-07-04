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
    
    def generate_3d_viewer(self, smiles: str, pdb_data: Optional[str] = None) -> Optional[str]:
        """
        生成3D分子查看器HTML
        
        Args:
            smiles: SMILES字符串
            pdb_data: PDB数据（可选）
        
        Returns:
            HTML字符串，失败返回None
        """
        try:
            if not HAS_PY3DMOL:
                logger.warning("py3Dmol未安装，无法生成3D查看器")
                return None
            
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
            
            # 创建3D查看器
            viewer = py3Dmol.view(width=600, height=400)
            viewer.addModel(sdf_data, 'sdf')
            viewer.setStyle({'stick': {}})
            viewer.zoomTo()
            
            # 如果有PDB数据，也添加到查看器
            if pdb_data:
                viewer.addModel(pdb_data, 'pdb')
                viewer.setStyle({'model': 1}, {'cartoon': {'color': 'spectrum'}})
            
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
    
    def get_molecule_properties(self, smiles: str) -> Dict[str, Any]:
        """
        获取分子性质
        
        Args:
            smiles: SMILES字符串
        
        Returns:
            分子性质字典
        """
        try:
            if not HAS_RDKIT:
                return {"error": "RDKit未安装"}
            
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                return {"error": "无效的SMILES"}
            
            return {
                "molecular_formula": rdMolDescriptors.CalcMolFormula(mol),
                "molecular_weight": round(Descriptors.MolWt(mol), 2),
                "logp": round(Descriptors.MolLogP(mol), 2),
                "hbd": Lipinski.NumHDonors(mol),
                "hba": Lipinski.NumHAcceptors(mol),
                "rotatable_bonds": Lipinski.NumRotatableBonds(mol),
                "tpsa": round(Descriptors.TPSA(mol), 2),
                "heavy_atoms": mol.GetNumHeavyAtoms(),
                "rings": rdMolDescriptors.CalcNumRings(mol),
                "aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol)
            }
            
        except Exception as e:
            logger.error(f"获取分子性质失败: {str(e)}")
            return {"error": str(e)}
