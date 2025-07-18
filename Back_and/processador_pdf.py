# /Back-and/processador_pdf.py

import os
import fitz  # PyMuPDF
import requests
import time

def contar_paginas_pdf(caminho_do_pdf):
    try:
        with fitz.open(caminho_do_pdf) as doc:
            return doc.page_count
    except Exception as e:
        print(f"Erro ao contar páginas do PDF: {e}")
        return 0

def extrair_texto_pagina_com_ocr(caminho_do_pdf, numero_pagina, api_key):
    # Esta função de fallback continua a mesma, pois o OCR não retorna coordenadas.
    # Ela será usada para PDFs que são apenas imagens.
    doc = None
    try:
        doc = fitz.open(caminho_do_pdf)
        if numero_pagina < 1 or numero_pagina > doc.page_count:
            raise ValueError(f"Número de página inválido: {numero_pagina}")

        pagina = doc.load_page(numero_pagina - 1)
        pix = pagina.get_pixmap(dpi=96) 
        bytes_imagem = pix.tobytes("png")
        
    except Exception as e:
        print(f"❌ Erro ao ler o PDF na página {numero_pagina}: {e}")
        raise e
    finally:
        if doc:
            doc.close()

    payload = {'apikey': api_key, 'language': 'por', 'isOverlayRequired': False}
    files = {'file': ('image.png', bytes_imagem, 'image/png')}
    
    max_tentativas = 3
    for tentativa in range(max_tentativas):
        try:
            print(f"Enviando página {numero_pagina} para a API de OCR (Tentativa {tentativa + 1})...")
            response = requests.post('https://api.ocr.space/parse/image', files=files, data=payload, timeout=60)
            response.raise_for_status()
            
            resultado = response.json()
            if resultado.get('IsErroredOnProcessing'):
                raise requests.exceptions.RequestException(f"Erro da API de OCR: {resultado.get('ErrorMessage')}")

            texto_extraido = resultado['ParsedResults'][0]['ParsedText']
            print(f"Texto da página {numero_pagina} recebido da API com sucesso.")
            # Retorna no formato esperado, mas sem coordenadas
            return {
                "texto_completo": texto_extraido.strip(),
                "palavras": [],
                "dimensoes": {"largura": 0, "altura": 0},
                "extraido_por_ocr": True
            }

        except requests.exceptions.RequestException as e:
            print(f"Tentativa de OCR {tentativa + 1} falhou: {e}")
            if tentativa < max_tentativas - 1:
                time.sleep(2 * (tentativa + 1))
            else:
                raise Exception(f"Falha ao processar a página {numero_pagina} com OCR.")

def extrair_dados_completos_pagina(caminho_do_pdf, numero_pagina, api_key):
    """
    Função principal atualizada.
    Extrai o texto completo para fala e uma lista de palavras com suas coordenadas.
    """
    try:
        doc = fitz.open(caminho_do_pdf)
        if numero_pagina < 1 or numero_pagina > doc.page_count:
            raise ValueError(f"Número de página inválido: {numero_pagina}")

        page = doc.load_page(numero_pagina - 1)
        
        # 1. Extrai a lista de palavras com coordenadas (x0, y0, x1, y1, word, block_no, line_no, word_no)
        lista_palavras = page.get_text("words")
        
        # Se o PDF tiver texto embutido, `lista_palavras` terá conteúdo
        if lista_palavras and len(lista_palavras) > 5:
            print(f"Extraindo dados da página {numero_pagina} diretamente do PDF.")
            
            # Formata os dados para enviar como JSON
            palavras_com_coords = [
                {
                    "texto": p[4],
                    "coords": {"x0": p[0], "y0": p[1], "x1": p[2], "y1": p[3]}
                }
                for p in lista_palavras
            ]

            # Extrai o texto completo para o expo-speech
            texto_completo = page.get_text("text")
            
            # Obtém as dimensões da página
            dimensoes = {"largura": page.rect.width, "altura": page.rect.height}
            
            doc.close()
            return {
                "texto_completo": texto_completo.strip(),
                "palavras": palavras_com_coords,
                "dimensoes": dimensoes,
                "extraido_por_ocr": False
            }
        else:
            # Fallback para OCR se não houver texto embutido
            print(f"Página {numero_pagina} não contém texto direto. Usando OCR.")
            doc.close()
            return extrair_texto_pagina_com_ocr(caminho_do_pdf, numero_pagina, api_key)

    except Exception as e:
        print(f"❌ Erro crítico ao processar a página {numero_pagina}: {e}")
        raise e