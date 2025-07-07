"""
药物化学引擎 - 处理蛋白质结构、口袋预测、化合物检索等功能
"""
import json
import subprocess
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple

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
