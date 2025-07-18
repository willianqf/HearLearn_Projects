import os
import time
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
import processador_pdf
import transcritor_audio
import gerador_pdf # NOVO: Importa o nosso novo módulo

OCR_API_KEY = os.getenv('OCR_SPACE_API_KEY')

FILE_LIFETIME_SECONDS = 3600
UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ... (Rotas existentes /iniciar_processamento, /uploads, /obter_dados_pagina, /transcrever_audio não mudam) ...
@app.route('/iniciar_processamento', methods=['POST'])
def iniciar_processamento():
    try:
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'erro': 'Nome de arquivo inválido'}), 400
        extensao = os.path.splitext(file.filename)[1]
        id_arquivo = f"{uuid.uuid4()}{extensao}"
        caminho_pdf_salvo = os.path.join(app.config['UPLOAD_FOLDER'], id_arquivo)
        file.save(caminho_pdf_salvo)
        total_paginas = processador_pdf.contar_paginas_pdf(caminho_pdf_salvo)
        if total_paginas == 0:
            os.remove(caminho_pdf_salvo)
            return jsonify({'erro': 'Não foi possível ler as páginas do PDF.'}), 400
        print(f"Arquivo recebido: {id_arquivo}, Total de páginas: {total_paginas}")
        return jsonify({
            'status': 'iniciado',
            'id_arquivo': id_arquivo,
            'total_paginas': total_paginas,
            'nome_original': file.filename
        }), 200
    except Exception as e:
        print(f"Erro em /iniciar_processamento: {e}")
        return jsonify({'erro': 'Erro interno ao iniciar o processamento.'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/obter_dados_pagina', methods=['POST'])
def obter_dados_pagina():
    if not OCR_API_KEY:
        return jsonify({'erro': 'Chave da API de OCR não configurada no servidor.'}), 500
    try:
        data = request.get_json()
        id_arquivo = data.get('id_arquivo')
        numero_pagina = data.get('numero_pagina')
        if not all([id_arquivo, numero_pagina]):
            return jsonify({'erro': 'Parâmetros ausentes'}), 400
        caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], id_arquivo)
        if not os.path.exists(caminho_pdf):
            return jsonify({'erro': 'Arquivo não encontrado no servidor'}), 404
        dados_da_pagina = processador_pdf.extrair_dados_completos_pagina(
            caminho_pdf,
            numero_pagina,
            OCR_API_KEY
        )
        return jsonify({'status': 'sucesso', 'dados': dados_da_pagina})
    except Exception as e:
        print(f"Erro final no endpoint /obter_dados_pagina: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/transcrever_audio', methods=['POST'])
def rota_transcrever_audio():
    if 'audio' not in request.files:
        return jsonify({'erro': 'Nenhum ficheiro de áudio enviado'}), 400
    file = request.files['audio']
    if not file or file.filename == '':
        return jsonify({'erro': 'Nome de ficheiro inválido'}), 400
    id_audio = f"audio_{uuid.uuid4()}.m4a"
    caminho_audio_salvo = os.path.join(app.config['UPLOAD_FOLDER'], id_audio)
    file.save(caminho_audio_salvo)
    texto_transcrito = ""
    try:
        texto_transcrito = transcritor_audio.transcrever_audio_para_texto(caminho_audio_salvo)
    finally:
        if os.path.exists(caminho_audio_salvo):
            os.remove(caminho_audio_salvo)
            print(f"🗑️ Ficheiro de áudio temporário removido: {id_audio}")
    return jsonify({'texto': texto_transcrito})

# --- NOVA ROTA PARA GERAR PDF ---
@app.route('/gerar_pdf', methods=['POST'])
def rota_gerar_pdf():
    data = request.get_json()
    texto = data.get('texto')

    if not texto:
        return jsonify({'erro': 'Nenhum texto foi fornecido'}), 400

    nome_ficheiro = gerador_pdf.criar_pdf_de_texto(texto, app.config['UPLOAD_FOLDER'])

    if nome_ficheiro:
        # Devolve a URL completa para o novo PDF
        url_pdf = f"{request.host_url}uploads/{nome_ficheiro}"
        return jsonify({'status': 'sucesso', 'url_pdf': url_pdf})
    else:
        return jsonify({'erro': 'Falha ao gerar o PDF no servidor'}), 500


# --- Limpeza de ficheiros (sem alterações) ---
def cleanup_old_files():
    print("Executando a tarefa de limpeza...")
    now = time.time()
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > FILE_LIFETIME_SECONDS:
                    os.remove(file_path)
                    print(f"Arquivo antigo removido: {filename}")
        except Exception as e:
            print(f"Erro ao limpar o arquivo {filename}: {e}")

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=cleanup_old_files, trigger="interval", minutes=30)
scheduler.start()
import atexit
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)