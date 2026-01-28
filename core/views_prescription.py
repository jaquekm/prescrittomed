from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import json

def gerar_receita_pdf(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        medicamentos = data.get('medicamentos', [])
        observacoes = data.get('observacoes', '')
        paciente_nome = data.get('paciente', 'Paciente Não Identificado')

        # Criar um buffer de bytes para o PDF
        buffer = io.BytesIO()
        
        # Configurar o Canvas (A4)
        p = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4
        
        # --- CABEÇALHO ---
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, altura - 50, "PrescrittoMED") # Seu Logo aqui
        
        p.setFont("Helvetica", 12)
        p.drawString(50, altura - 80, f"Paciente: {paciente_nome}")
        p.line(50, altura - 90, largura - 50, altura - 90) # Linha divisória

        # --- CORPO DA RECEITA (Medicamentos) ---
        y = altura - 130
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Prescrição:")
        y -= 25
        
        p.setFont("Helvetica", 12)
        for med in medicamentos:
            # Ex: Paracetamol 500mg
            texto_med = f"• {med['nome']} - {med['dosagem']}" 
            p.drawString(70, y, texto_med)
            y -= 15
            
            # Instruções de uso (ex: 1 cp a cada 8h)
            p.setFont("Helvetica-Oblique", 10)
            p.setFillColor(colors.darkgrey)
            p.drawString(90, y, f"Uso: {med['uso']}")
            p.setFillColor(colors.black)
            p.setFont("Helvetica", 12)
            y -= 25 # Espaço entre itens

        # --- OBSERVAÇÕES ---
        if observacoes:
            y -= 20
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, "Observações Clínicas:")
            y -= 20
            p.setFont("Helvetica", 11)
            
            # Dica: Para texto longo, precisaria usar textObject ou paragraph, 
            # mas aqui vai um exemplo simples:
            p.drawString(70, y, observacoes)

        # --- RODAPÉ ---
        p.setFont("Helvetica", 10)
        p.drawString(50, 50, "Documento gerado eletronicamente via PrescrittoMED AI.")
        
        # Finalizar PDF
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')