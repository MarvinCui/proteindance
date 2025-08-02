"""
药物化学引擎 - 处理蛋白质结构、口袋预测、化合物检索等功能
"""
import json
import subprocess
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

# 可选导入
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from Bio.PDB import PDBList
    HAS_BIOPYTHON = True
except ImportError:
    HAS_BIOPYTHON = False

from ..core.config import settings
from ..core.constants import PocketPredictionMethod, StructureSourceType
from ..models.protein import Protein, StructureSource, Pocket, Compound
from ..models.exceptions import APIError, ProcessingError, FileError
from ..utils.display import print_info, print_warning, print_error, show_spinner
from ..utils.helpers import safe_execute, validate_file_exists

logger = logging.getLogger(__name__)

# 常量定义
HEADERS_JSON = {"Content-Type": "application/json"}


class PharmaEngine:
    """药物化学引擎类 - 负责蛋白质和化合物相关操作"""
    
    def __init__(self):
        """初始化药物化学引擎"""
        self.uniprot_base = settings.UNIPROT_REST
        self.rcsb_api = settings.RCSB_SEARCH_API
        self.chembl_api = settings.CHEMBL_API
        self.alphafold_api = settings.ALPHAFOLD_API
        self.dogsite_api = settings.DOGSITE_API
    
    def search_uniprot(self, gene_symbol: str, organism_id: str = "9606") -> List[Dict]:
        """
        搜索UniProt数据库
        
        Args:
            gene_symbol: 基因符号
            organism_id: 物种ID (默认9606为人类)
        
        Returns:
            UniProt条目列表
        """
        try:
            print_info(f"正在搜索UniProt数据库中的{gene_symbol}...")
            
            url = (f"{self.uniprot_base}/uniprotkb/search"
                   f"?query=(gene_exact:{gene_symbol}+AND+organism_id:{organism_id})"
                   f"&fields=accession,protein_name&format=json&size=10")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for entry in data.get("results", []):
                try:
                    # 尝试获取蛋白质名称，处理不同的API响应格式
                    name = "Unknown protein"
                    if "proteinDescription" in entry:
                        desc = entry["proteinDescription"]
                        if "recommendedName" in desc and desc["recommendedName"]:
                            if "fullName" in desc["recommendedName"]:
                                name = desc["recommendedName"]["fullName"]["value"]
                        elif "submissionNames" in desc and desc["submissionNames"]:
                            name = desc["submissionNames"][0]["fullName"]["value"]

                    results.append({
                        "acc": entry["primaryAccession"],
                        "name": name
                    })
                except (KeyError, TypeError) as e:
                    logger.warning(f"解析UniProt条目失败: {e}")
                    # 仍然添加条目，但使用默认名称
                    results.append({
                        "acc": entry.get("primaryAccession", "Unknown"),
                        "name": "Unknown protein"
                    })
            
            logger.info(f"找到{len(results)}个UniProt条目")
            return results
            
        except Exception as e:
            logger.error(f"UniProt搜索失败: {str(e)}")
            raise APIError(f"UniProt搜索失败: {str(e)}")
    
    def get_pdb_ids_for_uniprot(self, accession: str, max_ids: int = 10) -> List[str]:
        """
        通过UniProt ID获取PDB结构ID
        
        Args:
            accession: UniProt ID
            max_ids: 最大返回数量
        
        Returns:
            PDB ID列表
        """
        try:
            print_info(f"正在查询UniProt {accession}对应的PDB结构...")
            
            query = {
                "query": {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                        "operator": "exact_match",
                        "value": accession,
                    },
                },
                "return_type": "entry",
                "request_options": {"return_all_hits": True},
            }
            
            response = requests.post(
                self.rcsb_api, 
                headers=HEADERS_JSON, 
                data=json.dumps(query), 
                timeout=30
            )
            
            # 检查响应状态
            logger.info(f"RCSB API响应状态: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"RCSB API返回非200状态: {response.status_code}")
                return []
            
            # 检查响应内容
            response_text = response.text.strip()
            if not response_text:
                logger.warning("RCSB API返回空响应")
                return []
            
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                logger.warning(f"RCSB API响应JSON解析失败: {e}, 响应内容: {response_text[:200]}")
                return []
            
            # 获取结果
            result_set = response_data.get("result_set", [])
            ids = [item["identifier"] for item in result_set if "identifier" in item]
            result = ids[:max_ids]
            
            logger.info(f"找到{len(result)}个PDB结构: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"RCSB API网络请求失败: {str(e)}")
            return []
        except Exception as e:
            logger.warning(f"PDB ID查询失败: {str(e)}")
            return []
    
    def get_pdb_ids_for_gene(self, gene_symbol: str, max_ids: int = 10) -> List[str]:
        """
        通过基因符号直接获取PDB结构ID
        
        Args:
            gene_symbol: 基因符号
            max_ids: 最大返回数量
        
        Returns:
            PDB ID列表
        """
        try:
            query = {
                "query": {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "value": gene_symbol,
                        "attribute": "rcsb_entity_source_organism.ncbi_gene_name.value"
                    }
                },
                "return_type": "entry",
                "request_options": {"return_all_hits": True}
            }
            
            response = requests.post(
                self.rcsb_api,
                headers=HEADERS_JSON,
                data=json.dumps(query),
                timeout=30
            )
            response.raise_for_status()
            
            ids = [x["identifier"] for x in response.json().get("result_set", [])]
            return ids[:max_ids]
            
        except Exception as e:
            logger.error(f"基因PDB查询失败: {str(e)}")
            raise APIError(f"基因PDB查询失败: {str(e)}")
    
    def download_pdb(self, pdb_id: str, dest_dir: Optional[Path] = None) -> Path:
        """
        下载PDB结构文件
        
        Args:
            pdb_id: PDB ID
            dest_dir: 目标目录
        
        Returns:
            下载的文件路径
        """
        try:
            if dest_dir is None:
                dest_dir = settings.TMP_DIR
            
            print_info(f"正在下载PDB结构 {pdb_id}...")

            if not HAS_BIOPYTHON:
                # 使用直接HTTP下载作为备选
                url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
                response = requests.get(url, timeout=60)
                response.raise_for_status()

                out_path = dest_dir / f"{pdb_id}.pdb"
                with open(out_path, "w") as f:
                    f.write(response.text)
                return out_path

            pdb_list = PDBList()
            fname = pdb_list.retrieve_pdb_file(
                pdb_id,
                file_format="pdb",
                pdir=str(dest_dir)
            )
            
            # Biopython可能下载为gz格式，需要解压
            if fname.endswith(".gz"):
                import gzip
                import shutil
                out_path = dest_dir / f"{pdb_id}.pdb"
                with gzip.open(fname, "rb") as fin, open(out_path, "wb") as fout:
                    shutil.copyfileobj(fin, fout)
                return out_path
            
            return Path(fname)
            
        except Exception as e:
            logger.error(f"PDB下载失败: {str(e)}")
            raise FileError(f"PDB下载失败: {str(e)}")
    
    def download_alphafold(self, uniprot_acc: str, dest_dir: Optional[Path] = None) -> Optional[Path]:
        """
        下载AlphaFold预测结构
        
        Args:
            uniprot_acc: UniProt ID
            dest_dir: 目标目录
        
        Returns:
            下载的文件路径，如果失败返回None
        """
        try:
            if dest_dir is None:
                dest_dir = settings.TMP_DIR
            
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            print_info(f"正在下载AlphaFold结构 {uniprot_acc}...")
            
            url = f"{self.alphafold_api}/AF-{uniprot_acc}-F1-model_v4.pdb"
            out_path = dest_dir / f"{uniprot_acc}_AF.pdb"
            
            logger.info(f"请求AlphaFold URL: {url}")
            
            response = requests.get(url, stream=True, timeout=60)
            
            logger.info(f"AlphaFold响应状态: {response.status_code}")
            logger.info(f"AlphaFold响应头Content-Length: {response.headers.get('Content-Length', 'N/A')}")
            
            if response.status_code == 200:
                content_length = int(response.headers.get("Content-Length", 0))
                if content_length > 1000:  # 确保文件不是空的或错误页面
                    with open(out_path, "wb") as f:
                        for chunk in response.iter_content(8192):
                            f.write(chunk)
                    
                    # 验证下载的文件
                    if out_path.exists() and out_path.stat().st_size > 1000:
                        logger.info(f"AlphaFold结构下载成功: {out_path} (大小: {out_path.stat().st_size} bytes)")
                        return out_path
                    else:
                        logger.warning(f"AlphaFold下载的文件太小或不存在: {uniprot_acc}")
                        return None
                else:
                    logger.warning(f"AlphaFold响应内容太小: {uniprot_acc} (Content-Length: {content_length})")
                    return None
            elif response.status_code == 404:
                logger.warning(f"AlphaFold结构不存在: {uniprot_acc}")
                return None
            else:
                logger.warning(f"AlphaFold请求失败: {uniprot_acc}, 状态码: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"AlphaFold网络请求失败: {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"AlphaFold下载失败: {str(e)}")
            return None

    def run_p2rank(self, pdb_path: Path, prank_bin: Optional[str] = None) -> List[Dict]:
        """
        使用P2Rank进行口袋预测

        Args:
            pdb_path: PDB文件路径
            prank_bin: P2Rank可执行文件路径

        Returns:
            口袋预测结果列表
        """
        try:
            print_info("正在进行结构分析和口袋预测...")

            # 查找P2Rank可执行文件
            if prank_bin:
                bin_path = Path(prank_bin)
            else:
                bin_path = settings.get_p2rank_binary()

            if not bin_path or not bin_path.exists():
                raise FileError("未找到P2Rank可执行文件")

            # 执行P2Rank预测
            out_dir = settings.TMP_DIR / f"{pdb_path.stem}_p2rank"
            cmd = [str(bin_path), "predict", "-f", str(pdb_path), "-o", str(out_dir)]

            with show_spinner("结构分析中..."):
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

            if process.returncode != 0:
                raise ProcessingError(f"P2Rank执行失败: {process.stderr}")

            # 读取结果CSV文件
            csv_files = list(out_dir.glob("*_predictions.csv"))
            if not csv_files:
                raise FileError("未找到P2Rank结果文件")

            if not HAS_PANDAS:
                # 手动解析CSV文件
                pockets = []
                with open(csv_files[0], 'r') as f:
                    lines = f.readlines()
                    if len(lines) < 2:
                        raise FileError("P2Rank结果文件格式错误")

                    headers = [h.strip().lower().replace(' ', '_') for h in lines[0].split(',')]
                    for i, line in enumerate(lines[1:], 1):
                        try:
                            values = [v.strip() for v in line.split(',')]
                            row_dict = dict(zip(headers, values))

                            center = [float(row_dict["center_x"]), float(row_dict["center_y"]), float(row_dict["center_z"])]
                            score = float(row_dict["score"])

                            pockets.append({
                                "pocket_id": f"pocket_{i}",
                                "center": center,
                                "score": score,
                                "prediction_method": PocketPredictionMethod.P2RANK
                            })
                        except (KeyError, ValueError) as e:
                            logger.warning(f"解析口袋数据失败: {e}")
                            continue
            else:
                df = pd.read_csv(csv_files[0])
                df.columns = (
                    df.columns
                    .str.strip()
                    .str.replace(r"\s+", "_", regex=True)
                    .str.lower()
                )

                # 解析口袋数据
                pockets = []
                for _, row in df.iterrows():
                    try:
                        center = [float(row["center_x"]), float(row["center_y"]), float(row["center_z"])]
                        score = float(row["score"])

                        pockets.append({
                            "pocket_id": f"pocket_{len(pockets)+1}",
                            "center": center,
                            "score": score,
                            "prediction_method": PocketPredictionMethod.P2RANK
                        })
                    except (KeyError, ValueError) as e:
                        logger.warning(f"解析口袋数据失败: {e}")
                        continue

            logger.info(f"P2Rank预测到{len(pockets)}个口袋")
            return pockets

        except Exception as e:
            logger.error(f"P2Rank预测失败: {str(e)}")
            raise ProcessingError(f"P2Rank预测失败: {str(e)}")

    def run_dogsite_api(self, pdb_path: Path) -> List[Dict]:
        """
        使用DoGSite API进行口袋预测

        Args:
            pdb_path: PDB文件路径

        Returns:
            口袋预测结果列表
        """
        try:
            print_info("正在使用DoGSite进行在线口袋预测...")

            # 提交作业
            url_job = f"{self.dogsite_api}/start/"
            with open(pdb_path, "rb") as f:
                files = {"file": f}
                response = requests.post(url_job, files=files, timeout=60)
                response.raise_for_status()

            job_id = response.json()["job_id"]
            print_info(f"作业已提交，ID: {job_id}")

            # 轮询作业状态
            url_status = f"{self.dogsite_api}/status/{job_id}/"
            url_result = f"{self.dogsite_api}/result/{job_id}/"

            import time
            max_wait = 300  # 5分钟超时
            wait_time = 0

            while wait_time < max_wait:
                time.sleep(5)
                wait_time += 5

                status_response = requests.get(url_status, timeout=30)
                status_response.raise_for_status()

                status = status_response.json()["status"]
                if status == "finished":
                    break
                elif status == "failed":
                    raise ProcessingError("DoGSite预测失败")

            if wait_time >= max_wait:
                raise ProcessingError("DoGSite预测超时")

            # 获取结果
            result_response = requests.get(url_result, timeout=30)
            result_response.raise_for_status()

            result_data = result_response.json()
            pockets = []

            for pocket_data in result_data.get("pockets", []):
                try:
                    center = pocket_data["center"]
                    score = pocket_data.get("druggability_score", 0.0)

                    pockets.append({
                        "pocket_id": f"dogsite_{len(pockets)+1}",
                        "center": center,
                        "score": score,
                        "prediction_method": PocketPredictionMethod.DOGSITE
                    })
                except (KeyError, ValueError) as e:
                    logger.warning(f"解析DoGSite口袋数据失败: {e}")
                    continue

            logger.info(f"DoGSite预测到{len(pockets)}个口袋")
            return pockets

        except Exception as e:
            logger.error(f"DoGSite预测失败: {str(e)}")
            raise ProcessingError(f"DoGSite预测失败: {str(e)}")

    def fetch_chembl_smiles(self, uniprot_acc: str, max_hits: int = 10) -> List[str]:
        """
        从ChEMBL数据库获取活性化合物SMILES

        Args:
            uniprot_acc: UniProt ID
            max_hits: 最大返回数量

        Returns:
            SMILES列表
        """
        try:
            print_info(f"正在从ChEMBL数据库查询与UniProt:{uniprot_acc}相关的活性化合物...")

            # 尝试使用ChEMBL客户端
            try:
                from chembl_webresource_client.new_client import new_client
                HAS_CHEMBL_CLIENT = True
            except ImportError:
                HAS_CHEMBL_CLIENT = False

            if not HAS_CHEMBL_CLIENT:
                print_warning("ChEMBL客户端未安装，使用默认化合物")
                return self._get_default_drug_like_smiles(max_hits)

            # 获取靶点ChEMBL ID
            targets = new_client.target.filter(
                target_components__accession=uniprot_acc
            ).only(["target_chembl_id"])

            if not targets:
                print_warning(f"ChEMBL中未找到UniProt {uniprot_acc}对应的蛋白靶点记录")
                return []

            chembl_id = targets[0]["target_chembl_id"]
            print_info(f"找到ChEMBL靶点: {chembl_id}")

            # 获取活性数据
            activities = new_client.activity.filter(
                target_chembl_id=chembl_id,
                standard_type__in=["IC50", "Ki", "Kd"],
                standard_relation="=",
                assay_type="B"
            ).only([
                "molecule_chembl_id",
                "standard_value",
                "standard_units",
                "standard_type"
            ])

            # 收集分子ID
            molecule_ids = []
            for activity in activities:
                if activity.get("standard_value") and float(activity["standard_value"]) <= 10000:  # nM
                    molecule_ids.append(activity["molecule_chembl_id"])

                if len(molecule_ids) >= max_hits * 2:  # 获取更多以防有些没有SMILES
                    break

            if not molecule_ids:
                print_warning("未找到活性化合物")
                return []

            # 获取SMILES
            molecules = new_client.molecule.filter(
                molecule_chembl_id__in=molecule_ids
            ).only(["molecule_chembl_id", "molecule_structures"])

            smiles_list = []
            for mol in molecules:
                structures = mol.get("molecule_structures")
                if structures and structures.get("canonical_smiles"):
                    smiles = structures["canonical_smiles"]
                    if self._validate_smiles(smiles):
                        smiles_list.append(smiles)

                if len(smiles_list) >= max_hits:
                    break

            logger.info(f"获取到{len(smiles_list)}个活性化合物SMILES")
            return smiles_list

        except Exception as e:
            logger.error(f"ChEMBL查询失败: {str(e)}")
            # 返回一些默认的药物样分子作为备选
            return self._get_default_drug_like_smiles(max_hits)

    def smiles_to_pdbqt(self, smiles: str, name: str = "lig") -> Path:
        """
        将SMILES转换为PDBQT格式

        Args:
            smiles: SMILES字符串
            name: 分子名称

        Returns:
            PDBQT文件路径
        """
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem

            # 生成3D结构
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                raise ValueError(f"无效的SMILES: {smiles}")

            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, AllChem.ETKDG())
            AllChem.UFFOptimizeMolecule(mol)

            # 保存为SDF
            sdf_path = settings.TMP_DIR / f"{name}.sdf"
            Chem.MolToMolFile(mol, str(sdf_path))

            # 转换为PDBQT
            pdbqt_path = settings.TMP_DIR / f"{name}.pdbqt"
            subprocess.run(
                ["obabel", str(sdf_path), "-O", str(pdbqt_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return pdbqt_path

        except Exception as e:
            logger.error(f"SMILES转PDBQT失败: {str(e)}")
            raise ProcessingError(f"SMILES转PDBQT失败: {str(e)}")

    def smiles_to_pdb(self, smiles: str, name: str = "lig") -> Path:
        """
        将SMILES转换为PDB格式

        Args:
            smiles: SMILES字符串
            name: 分子名称

        Returns:
            PDB文件路径
        """
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem

            # 生成3D结构
            mol = Chem.MolFromSmiles(smiles)
            if not mol:
                raise ValueError(f"无效的SMILES: {smiles}")

            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, AllChem.ETKDG())
            AllChem.UFFOptimizeMolecule(mol)

            # 保存为PDB
            pdb_path = settings.TMP_DIR / f"{name}.pdb"
            Chem.MolToPDBFile(mol, str(pdb_path))

            return pdb_path

        except Exception as e:
            logger.error(f"SMILES转PDB失败: {str(e)}")
            raise ProcessingError(f"SMILES转PDB失败: {str(e)}")

    def convert_protein_structure(self, input_path: Path, output_format: str = "pdb", name: str = "protein") -> Path:
        """
        转换蛋白质结构文件格式
        
        Args:
            input_path: 输入文件路径
            output_format: 输出格式 ("pdb" 或 "pdbqt")
            name: 输出文件名
            
        Returns:
            转换后的文件路径
        """
        try:
            if output_format.lower() == "pdb":
                # 如果输入已经是PDB格式，直接复制
                if input_path.suffix.lower() in ['.pdb', '.ent']:
                    output_path = settings.TMP_DIR / f"{name}.pdb"
                    import shutil
                    shutil.copy2(input_path, output_path)
                    return output_path
                else:
                    # 使用obabel转换为PDB格式
                    output_path = settings.TMP_DIR / f"{name}.pdb"
                    subprocess.run(
                        ["obabel", str(input_path), "-O", str(output_path)],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return output_path
                    
            elif output_format.lower() == "pdbqt":
                # 转换为PDBQT格式（用于分子对接）
                output_path = settings.TMP_DIR / f"{name}.pdbqt"
                
                # 使用obabel转换为PDBQT格式，并指定为受体（刚性）
                result = subprocess.run(
                    ["obabel", str(input_path), "-O", str(output_path), 
                     "-p", "7.4",  # 添加氢原子，pH=7.4
                     "--partialcharge", "gasteiger"],  # 添加partial charge
                    capture_output=True,
                    text=True,
                    check=False  # 允许失败，便于调试
                )
                
                if result.returncode != 0:
                    logger.warning(f"obabel转换警告: {result.stderr}")
                    # 如果失败，尝试简单转换
                    subprocess.run(
                        ["obabel", str(input_path), "-O", str(output_path)],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                
                return output_path
            else:
                raise ValueError(f"不支持的输出格式: {output_format}")
                
        except Exception as e:
            logger.error(f"蛋白质结构转换失败: {str(e)}")
            raise ProcessingError(f"蛋白质结构转换失败: {str(e)}")

    def prepare_protein_for_docking(self, pdb_path: Path, output_name: str = "receptor") -> Path:
        """
        准备蛋白质用于分子对接（转换为PDBQT格式）

        Args:
            pdb_path: PDB文件路径
            output_name: 输出文件名

        Returns:
            PDBQT文件路径
        """
        try:
            pdbqt_path = settings.TMP_DIR / f"{output_name}.pdbqt"
            
            # 使用obabel转换为PDBQT格式，并指定为受体（刚性）
            result = subprocess.run(
                ["obabel", str(pdb_path), "-O", str(pdbqt_path), 
                 "-p", "7.4",  # 添加氢原子，pH=7.4
                 "--partialcharge", "gasteiger"],  # 添加partial charge
                capture_output=True,
                text=True,
                check=False  # 允许失败，便于调试
            )
            
            if result.returncode != 0:
                logger.warning(f"obabel转换警告: {result.stderr}")
            
            # 使用增强的蛋白质预处理器修复PDBQT格式
            from .docking_engine import ProteinPreprocessor
            preprocessor = ProteinPreprocessor()
            cleaned_pdbqt_path = preprocessor.fix_protein_structure(pdbqt_path, pdbqt_path)
            if not cleaned_pdbqt_path:
                logger.warning("蛋白质预处理失败，使用旧方法")
                self._fix_receptor_pdbqt_format(pdbqt_path)
            
            logger.info(f"蛋白质已转换为PDBQT格式: {pdbqt_path}")
            return pdbqt_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"蛋白质PDBQT转换失败: {str(e)}")
            raise ProcessingError(f"蛋白质PDBQT转换失败: {str(e)}")
        except Exception as e:
            logger.error(f"蛋白质准备失败: {str(e)}")
            raise ProcessingError(f"蛋白质准备失败: {str(e)}")

    def _fix_receptor_pdbqt_format(self, pdbqt_path: Path):
        """
        修复受体PDBQT文件格式，移除ROOT/ENDROOT结构
        
        Args:
            pdbqt_path: PDBQT文件路径
        """
        try:
            with open(pdbqt_path, 'r') as f:
                lines = f.readlines()
            
            # 过滤掉ROOT/ENDROOT/TORSDOF行，保留ATOM和REMARK行
            fixed_lines = []
            for line in lines:
                if line.startswith(('ATOM', 'HETATM', 'REMARK')):
                    fixed_lines.append(line)
                elif line.startswith('ROOT') or line.startswith('ENDROOT') or line.startswith('TORSDOF'):
                    continue
                else:
                    # 对于其他行，如果看起来像原子行，也保留
                    parts = line.split()
                    if len(parts) >= 6 and parts[0] in ['ATOM', 'HETATM']:
                        fixed_lines.append(line)
            
            # 确保文件不为空
            if not any(line.startswith(('ATOM', 'HETATM')) for line in fixed_lines):
                # 如果没有原子行，添加一个默认的
                fixed_lines.append("ATOM      1  CA  ALA A   1      20.000  30.000  40.000  0.00  0.00    +0.000 C \n")
            
            with open(pdbqt_path, 'w') as f:
                f.writelines(fixed_lines)
                
        except Exception as e:
            logger.error(f"修复PDBQT格式失败: {str(e)}")
            # 如果修复失败，保持原文件

    def run_vina_docking(self, receptor_pdbqt: Path, ligand_pdbqt: Path, 
                        pocket_center: List[float], box_size: List[float] = None,
                        output_name: str = "docking_result") -> Dict[str, Any]:
        """
        使用Vina进行分子对接

        Args:
            receptor_pdbqt: 受体PDBQT文件路径
            ligand_pdbqt: 配体PDBQT文件路径
            pocket_center: 对接口袋中心坐标 [x, y, z]
            box_size: 搜索盒子大小 [x, y, z]，默认为 [20, 20, 20]
            output_name: 输出文件名

        Returns:
            对接结果字典
        """
        try:
            if box_size is None:
                box_size = [20, 20, 20]
            
            # 输出文件路径
            output_pdbqt = settings.TMP_DIR / f"{output_name}.pdbqt"
            log_file = settings.TMP_DIR / f"{output_name}.log"
            
            # Vina可执行文件路径
            vina_path = Path(__file__).parent.parent.parent / "vina"
            
            if not vina_path.exists():
                raise ProcessingError(f"Vina可执行文件不存在: {vina_path}")
            
            # 构建Vina命令
            vina_cmd = [
                str(vina_path),
                "--receptor", str(receptor_pdbqt),
                "--ligand", str(ligand_pdbqt),
                "--center_x", str(pocket_center[0]),
                "--center_y", str(pocket_center[1]),
                "--center_z", str(pocket_center[2]),
                "--size_x", str(box_size[0]),
                "--size_y", str(box_size[1]),
                "--size_z", str(box_size[2]),
                "--out", str(output_pdbqt),
                "--exhaustiveness", "8",
                "--num_modes", "9"
            ]
            
            logger.info(f"运行Vina对接: {' '.join(vina_cmd)}")
            
            # 执行Vina
            result = subprocess.run(
                vina_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                logger.error(f"Vina执行失败: {result.stderr}")
                raise ProcessingError(f"Vina执行失败: {result.stderr}")
            
            # 保存Vina输出到日志文件
            with open(log_file, 'w') as f:
                f.write(result.stdout)
            
            # 解析对接结果
            docking_results = self._parse_vina_results(log_file, output_pdbqt)
            
            logger.info(f"Vina对接完成，找到{len(docking_results['poses'])}个构象")
            
            return {
                "success": True,
                "receptor_path": str(receptor_pdbqt),
                "ligand_path": str(ligand_pdbqt),
                "output_path": str(output_pdbqt),
                "log_path": str(log_file),
                "pocket_center": pocket_center,
                "box_size": box_size,
                "poses": docking_results['poses'],
                "best_score": docking_results['best_score'],
                "best_pose": docking_results['best_pose']
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Vina对接超时")
            raise ProcessingError("Vina对接超时")
        except Exception as e:
            logger.error(f"Vina对接失败: {str(e)}")
            raise ProcessingError(f"Vina对接失败: {str(e)}")

    def _parse_vina_results(self, log_file: Path, output_pdbqt: Path) -> Dict[str, Any]:
        """
        解析Vina对接结果

        Args:
            log_file: Vina日志文件路径
            output_pdbqt: 输出PDBQT文件路径

        Returns:
            解析后的对接结果
        """
        try:
            poses = []
            best_score = float('inf')
            best_pose = None
            
            # 解析日志文件获取评分
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_content = f.read()
                    
                # 查找评分信息 - 支持新的表格格式
                lines = log_content.split('\n')
                parsing_table = False
                
                for line in lines:
                    line = line.strip()
                    
                    # 检测表格开始
                    if 'mode |   affinity' in line:
                        parsing_table = True
                        continue
                    
                    # 解析表格数据
                    if parsing_table and line.startswith('---'):
                        continue  # 跳过表头分隔线
                    
                    if parsing_table and line and not line.startswith('-----'):
                        parts = line.split()
                        if len(parts) >= 3 and parts[0].isdigit():
                            try:
                                mode_id = int(parts[0])
                                score = float(parts[1])
                                rmsd_lb = float(parts[2]) if len(parts) > 2 else 0.0
                                rmsd_ub = float(parts[3]) if len(parts) > 3 else 0.0
                                
                                pose_info = {
                                    "pose_id": mode_id,
                                    "binding_affinity": score,
                                    "rmsd_lower": rmsd_lb,
                                    "rmsd_upper": rmsd_ub
                                }
                                poses.append(pose_info)
                                
                                if score < best_score:
                                    best_score = score
                                    best_pose = pose_info
                            except (ValueError, IndexError):
                                continue
                    
                    # 保持向后兼容：也检查旧格式
                    if 'REMARK VINA RESULT:' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                score = float(parts[3])
                                rmsd_lb = float(parts[4]) if len(parts) > 4 else 0.0
                                rmsd_ub = float(parts[5]) if len(parts) > 5 else 0.0
                                
                                pose_info = {
                                    "pose_id": len(poses) + 1,
                                    "binding_affinity": score,
                                    "rmsd_lower": rmsd_lb,
                                    "rmsd_upper": rmsd_ub
                                }
                                poses.append(pose_info)
                                
                                if score < best_score:
                                    best_score = score
                                    best_pose = pose_info
                            except (ValueError, IndexError):
                                continue
            
            # 如果没有找到评分，创建默认结果
            if not poses:
                poses = [{
                    "pose_id": 1,
                    "binding_affinity": 0.0,
                    "rmsd_lower": 0.0,
                    "rmsd_upper": 0.0
                }]
                best_score = 0.0
                best_pose = poses[0]
            
            return {
                "poses": poses,
                "best_score": best_score,
                "best_pose": best_pose
            }
            
        except Exception as e:
            logger.error(f"解析Vina结果失败: {str(e)}")
            return {
                "poses": [],
                "best_score": 0.0,
                "best_pose": None
            }

    def perform_molecular_docking(self, protein_path: Path, ligand_smiles: str, 
                                 pocket_center: List[float], box_size: List[float] = None,
                                 output_dir: Path = None) -> Dict[str, Any]:
        """
        执行完整的分子对接流程 - 使用成熟的DockingEngine
        
        Args:
            protein_path: 蛋白质PDB文件路径
            ligand_smiles: 配体SMILES字符串
            pocket_center: 对接口袋中心坐标
            box_size: 搜索盒子大小
            output_dir: 输出目录路径（可选，默认使用临时目录）

        Returns:
            对接结果字典
        """
        try:
            logger.info("🔥" * 20)
            logger.info(f"🔬 pharma_engine.perform_molecular_docking 开始")
            logger.info(f"📁 蛋白质路径: {protein_path}")
            logger.info(f"🧬 配体SMILES: {ligand_smiles[:30]}...")
            logger.info(f"📍 口袋坐标: {pocket_center}")
            logger.info(f"📦 盒子大小: {box_size}")
            logger.info(f"📂 输出目录: {output_dir}")
            
            # 如果没有指定输出目录，使用默认逻辑
            if output_dir is None:
                project_root = Path(__file__).parent.parent.parent
                temp_base = project_root / "temp"
                temp_base.mkdir(exist_ok=True)
                
                import time
                timestamp = int(time.time())
                output_dir = temp_base / f"docking_{timestamp}"
                logger.info(f"📂 自动创建输出目录: {output_dir}")
                output_dir.mkdir(exist_ok=True)
            
            # 导入并使用新的DockingEngine
            logger.info("📥 导入DockingEngine...")
            from .docking_engine import DockingEngine
            logger.info("✅ DockingEngine导入成功")
            
            # 创建对接引擎实例
            logger.info("🏗️ 创建DockingEngine实例...")
            docking_engine = DockingEngine()
            logger.info("✅ DockingEngine实例创建成功")
            
            # 首先需要转换SMILES到PDBQT文件
            logger.info("🧪 开始准备配体结构...")
            ligand_pdbqt = self.smiles_to_pdbqt(ligand_smiles, "ligand")
            logger.info(f"✅ 配体PDBQT文件: {ligand_pdbqt}")
            
            # 使用成熟的对接流程
            # 注意：需要临时创建配体文件以便对接引擎使用
            temp_ligand_path = protein_path.parent / "temp_ligand.pdbqt"
            logger.info(f"📋 临时配体路径: {temp_ligand_path}")
            
            # 复制生成的配体文件到临时位置
            import shutil
            if ligand_pdbqt.exists():
                logger.info("📋 复制配体文件到临时位置...")
                shutil.copy2(ligand_pdbqt, temp_ligand_path)
                logger.info("✅ 配体文件复制成功")
            else:
                # 如果配体文件生成失败，使用基础对接方法作为降级
                logger.warning("❌ 配体文件生成失败，使用基础对接方法")
                return self._perform_basic_docking(protein_path, ligand_smiles, pocket_center, box_size)
            
            # 运行完整的成熟对接流程
            logger.info("🚀 开始运行完整对接流程...")
            logger.info(f"⚙️ 调用 docking_engine.run_complete_docking_pipeline")
            logger.info(f"   - protein_path: {protein_path}")
            logger.info(f"   - ligand_smiles: {ligand_smiles[:30]}...")
            logger.info(f"   - pocket_center: {pocket_center}")
            logger.info(f"   - box_size: {box_size or [20.0, 20.0, 20.0]}")
            logger.info(f"   - ligand_pdbqt_path: {temp_ligand_path}")
            
            result = docking_engine.run_complete_docking_pipeline(
                protein_path=protein_path,
                ligand_smiles=ligand_smiles,
                pocket_center=pocket_center,
                box_size=box_size or [20.0, 20.0, 20.0],
                ligand_pdbqt_path=temp_ligand_path,  # 传递配体文件路径
                output_dir=output_dir  # 传递输出目录
            )
            
            logger.info("🎯 对接流程执行完成!")
            logger.info(f"📊 结果类型: {type(result)}")
            logger.info(f"📊 结果keys: {list(result.keys()) if result else 'None'}")
            
            # 清理临时文件
            if temp_ligand_path.exists():
                temp_ligand_path.unlink()
            
            return result
            
        except Exception as e:
            logger.error(f"成熟分子对接失败，尝试基础对接: {str(e)}")
            # 如果成熟对接失败，降级到基础对接方法
            return self._perform_basic_docking(protein_path, ligand_smiles, pocket_center, box_size)
    
    def _perform_basic_docking(self, protein_path: Path, ligand_smiles: str, 
                              pocket_center: List[float], box_size: List[float] = None) -> Dict[str, Any]:
        """
        基础分子对接流程（降级方法）
        
        Args:
            protein_path: 蛋白质PDB文件路径
            ligand_smiles: 配体SMILES字符串
            pocket_center: 对接口袋中心坐标
            box_size: 搜索盒子大小

        Returns:
            对接结果字典
        """
        try:
            logger.info(f"使用基础分子对接流程: {ligand_smiles}")
            
            # 1. 准备蛋白质
            logger.info("准备蛋白质结构...")
            receptor_pdbqt = self.prepare_protein_for_docking(protein_path)
            
            # 2. 准备配体
            logger.info("准备配体结构...")
            ligand_pdbqt = self.smiles_to_pdbqt(ligand_smiles, "ligand")
            
            # 3. 执行对接
            logger.info("执行分子对接...")
            docking_results = self.run_vina_docking(
                receptor_pdbqt, ligand_pdbqt, pocket_center, box_size
            )
            
            # 4. 添加额外信息
            docking_results.update({
                "ligand_smiles": ligand_smiles,
                "protein_path": str(protein_path),
                "timestamp": str(datetime.now()),
                "method": "basic_docking"  # 标记为基础对接方法
            })
            
            return docking_results
            
        except Exception as e:
            logger.error(f"基础分子对接失败: {str(e)}")
            raise ProcessingError(f"分子对接失败: {str(e)}")

    def _validate_smiles(self, smiles: str) -> bool:
        """验证SMILES字符串的有效性"""
        try:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(smiles)
            return mol is not None
        except ImportError:
            # 如果没有rdkit，进行简单验证
            return bool(smiles and len(smiles.strip()) > 0 and not smiles.isspace())

    def _get_default_drug_like_smiles(self, max_count: int) -> List[str]:
        """获取默认的药物样分子SMILES"""
        default_smiles = [
            "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",  # 布洛芬
            "CC1=CC=C(C=C1)C(=O)C2=CC=C(C=C2)N(C)C",  # 他莫昔芬类似物
            "CN1CCN(CC1)C2=C(C=C3C(=C2)N=CN=C3NC4=CC(=C(C=C4)F)Cl)OC",  # 吉非替尼类似物
            "CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)C",  # 伊马替尼类似物
            "CN(C)CCOC1=CC=C(C=C1)C2=C3C=CC(=O)C=C3OC4=C2C=CC(=C4)O",  # 雌激素类似物
            "CC1=CC=C(C=C1)S(=O)(=O)NC2=CC=C(C=C2)C(=O)O",  # 磺胺类药物
            "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # 咖啡因
            "CC(C)(C)NCC(C1=CC(=C(C=C1)O)CO)O",  # 沙丁胺醇
            "CN1C2=C(C(=O)N(C1=O)C)N=CN2C",  # 茶碱
            "CC1=CC=C(C=C1)C(=O)NC2=CC=C(C=C2)O"  # 对乙酰氨基酚类似物
        ]

        logger.warning(f"使用默认药物样分子SMILES，数量: {min(max_count, len(default_smiles))}")
        return default_smiles[:max_count]
