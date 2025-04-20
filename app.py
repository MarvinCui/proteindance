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
    entry_name = request.form.get('entry_name')  # Passed from previous step

    if not accession:
        flash('请提供一个 UniProt Accession。', 'error')
        return redirect(url_for('index'))  # Assuming 'index' is your search/home page

    # Fetch FASTA sequence
    fasta = fetch_fasta(accession)
    if not fasta:
        flash(f'未能获取 {accession} 的 FASTA 序列。', 'warning')
        fasta = "无法获取 FASTA 序列。"  # Placeholder text

    # Get AlphaFold predictions and convert generator/iterable to list
    prediction_list = []
    try:
        # Call the function and immediately convert its result (generator/iterable) to a list
        raw_predictions = services.predict_structure(accession)
        prediction_list = list(raw_predictions)  # Convert generator to list here!

        for i, pred in enumerate(raw_predictions, start=1):
            print(f"--- Prediction #{i} ---")
            for key, value in pred.items():
                print(f"{key!r}: {value!r}")

        print(prediction_list)
        # Now you can safely check the length for debugging/logging
        print(f"Retrieved {len(prediction_list)} predictions for {accession}")

    except Exception as e:
        print(f"Error retrieving AlphaFold predictions for {accession}: {e}")
        flash(f'获取 AlphaFold 预测时出错: {e}', 'error')
        # Keep prediction_list as empty, prediction_data will be None

    # Determine the actual data to pass to the template (the first prediction dict or None)
    prediction_data = None
    if prediction_list:
        # If the list is not empty, take the first prediction dictionary
        prediction_data = prediction_list[0]
    else:
        # If the list is empty (either from API or after an error), flash a warning
        # only if FASTA was successfully fetched.
        if fasta != "无法获取 FASTA 序列。":
            flash(f'未能找到 {accession} 的 AlphaFold 预测。', 'warning')

    # Make entry_name more robust if not provided
    if not entry_name:
        entry_name = f"UniProt {accession}"  # Default name

    # Pass the prediction dictionary (or None) to the template, NOT the list
    return render_template(
        'result.html',
        entry_name=entry_name,
        accession=accession,
        fasta=fasta,
        prediction_data=prediction_data  # Pass the single dictionary or None
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 6655)))
