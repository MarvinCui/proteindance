from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv

import services
from services import (
    initialize_deepseek_client,
    get_target_proteins,
    search_uniprot,
    fetch_fasta,
    predict_structure
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'replace-with-secure-random')

# Configure DeepSeek
DS_MODEL_NAME = os.getenv('DS_MODEL_NAME', 'deepseek-chat')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        disease = request.form.get('disease', '').strip()
        if not disease:
            flash('请输入疾病名称。', 'error')
            return redirect(url_for('index'))
        return redirect(url_for('select_protein', disease=disease))
    return render_template('index.html')
    # return "hello world"


@app.route('/proteins/<disease>')
def select_protein(disease):
    key = services.load_api_key()
    client = initialize_deepseek_client(key)
    print("initialize_deepseek_client")
    if not client:
        flash('DeepSeek 客户端初始化失败，请检查配置。', 'error')
        return redirect(url_for('index'))
    proteins = get_target_proteins(client, DS_MODEL_NAME, disease)
    if not proteins:
        flash('未能获取候选蛋白，请稍后重试。', 'error')
        return redirect(url_for('index'))
    return render_template('proteins.html', disease=disease, proteins=proteins)


@app.route('/candidates', methods=['POST'])
def candidates():
    for key, value in request.form.items():
        print(f"{key} = {value}")
    keyword = request.form.get('keyword')
    if not keyword:
        flash('参数丢失，请重试。', 'error')
        return redirect(url_for('index'))

    candidates = search_uniprot(keyword)
    if not candidates:
        flash('未找到匹配的 UniProt 条目。', 'error')
        return redirect(url_for('index'))
    return render_template('candidates.html', candidates=candidates)


@app.route('/result', methods=['POST'])
def result():
    accession = request.form.get('accession')
    entry_name = request.form.get('entry_name')
    if not accession:
        flash('请选择一个条目。', 'error')
        return redirect(url_for('index'))

    fasta = fetch_fasta(accession)
    if not fasta:
        flash('无法获取 FASTA 序列。', 'error')
        return redirect(url_for('index'))

    pdb_urls = predict_structure(accession)
    return render_template('result.html', entry_name=entry_name, accession=accession, fasta=fasta, pdb_urls=pdb_urls[0])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 6655)))
