import py3Dmol
view = py3Dmol.view(query='./AF-P00520-F1-model_v4.pdb')
view.setStyle({'cartoon':{}})
view.png()  # 返回 base64 PNG 数据
