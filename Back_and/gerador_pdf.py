from fpdf import FPDF
import os
import uuid

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Documento Gerado por HearLearn', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def criar_pdf_de_texto(texto, pasta_uploads):
    """
    Cria um ficheiro PDF a partir de uma string de texto.
    """
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # A função multi_cell lida automaticamente com quebras de linha
        pdf.multi_cell(0, 10, txt=texto)

        # Gera um nome de ficheiro único e guarda o PDF
        nome_ficheiro_pdf = f"ditado_{uuid.uuid4()}.pdf"
        caminho_completo = os.path.join(pasta_uploads, nome_ficheiro_pdf)
        
        pdf.output(caminho_completo)
        
        print(f"📄 PDF gerado com sucesso em: {caminho_completo}")
        return nome_ficheiro_pdf

    except Exception as e:
        print(f"❌ Erro ao gerar o PDF: {e}")
        return None
