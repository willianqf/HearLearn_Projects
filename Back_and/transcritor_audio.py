import whisper
import os

# Carrega o modelo Whisper. O modelo 'base' é um bom equilíbrio entre
# velocidade e precisão para um servidor. Ele será descarregado na primeira vez.
try:
    print("🧠 Carregando o modelo Whisper (modelo: base)...")
    model = whisper.load_model("tiny")
    print("✅ Modelo Whisper carregado com sucesso.")
except Exception as e:
    print(f"❌ Erro crítico ao carregar o modelo Whisper: {e}")
    model = None

def transcrever_audio_para_texto(caminho_do_audio):
    """
    Recebe o caminho de um ficheiro de áudio e retorna o texto transcrito usando Whisper.
    """
    if not model:
        return "[Erro: O modelo de transcrição não pôde ser carregado no servidor.]"

    print(f"🎤 A iniciar transcrição com Whisper para: {caminho_do_audio}")

    try:
        # A função transcribe do Whisper lida com a conversão e processamento
        result = model.transcribe(caminho_do_audio, language="pt", fp16=False)
        
        texto_final = result.get("text", "").strip()

        if texto_final:
            print(f"✅ Transcrição concluída: '{texto_final}'")
        else:
            print("⚠️ A transcrição não produziu texto.")
            texto_final = "[Não foi possível detetar fala no áudio.]"
        
        return texto_final

    except Exception as e:
        print(f"❌ Erro durante a transcrição com Whisper: {e}")
        return f"[Erro no processo de transcrição: {e}]"