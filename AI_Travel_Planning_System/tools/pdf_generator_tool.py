import html
import re
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from datetime import datetime
from zoneinfo import ZoneInfo

def parse_and_format_text(text, styles):
    """Parses markdown text into styled ReportLab paragraphs and tables."""
    elements = []
    lines = str(text).split('\n')
    
    table_data = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_table:
                elements.append(build_styled_table(table_data, styles))
                table_data = []
                in_table = False
            else:
                elements.append(Spacer(1, 8))
            continue
            
        # Detect Markdown Tables
        if '|' in line:
            in_table = True
            # Clean up the row and split into columns
            row_cells = [cell.strip() for cell in line.strip('|').split('|')]
            
            # Skip markdown separator lines like |---|---|
            if all(all(c in '-:' for c in cell) for cell in row_cells if cell):
                continue
            
            # Escape HTML, then apply bold formatting to table cells
            formatted_row = []
            for cell in row_cells:
                safe_cell = html.escape(cell)
                bold_cell = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_cell)
                formatted_row.append(Paragraph(bold_cell, styles["TableText"]))
            
            table_data.append(formatted_row)
        else:
            if in_table:
                elements.append(build_styled_table(table_data, styles))
                table_data = []
                in_table = False
            
            # Escape HTML, then apply bold formatting to normal text
            safe_line = html.escape(line)
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_line)
            
            # Detect Markdown Headers
            if formatted_line.startswith('### '):
                elements.append(Paragraph(formatted_line[4:], styles["Heading3"]))
            elif formatted_line.startswith('## '):
                elements.append(Paragraph(formatted_line[3:], styles["Heading2"]))
            elif formatted_line.startswith('# '):
                elements.append(Paragraph(formatted_line[2:], styles["Heading1"]))
            else:
                elements.append(Paragraph(formatted_line, styles["BodyText"]))
                
    # Catch any table that ends at the very bottom of the text
    if in_table and table_data:
        elements.append(build_styled_table(table_data, styles))
        
    return elements

def build_styled_table(table_data, styles):
    """Builds a beautifully formatted ReportLab table."""
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")), # Dark blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#DEE2E6")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F8F9FA"), colors.white]),
    ]))
    return t

def generate_travel_pdf(pdf_path, user_query, thread_id, collected):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    # 1. Setup Custom Typography
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=24, textColor=colors.HexColor("#2C3E50"), spaceAfter=20))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor("#1A5276"), spaceBefore=20, spaceAfter=10))
    styles.add(ParagraphStyle(name='TableText', parent=styles['BodyText'], fontSize=9, leading=12))

    story = []

    # 2. Header Information
    story.append(Paragraph("AI Travel Planner Report", styles["CustomTitle"]))
    story.append(Paragraph(f"<b>User Query:</b> {html.escape(str(user_query))}", styles["BodyText"]))
    story.append(Paragraph(f"<b>User ID:</b> {html.escape(str(thread_id))}", styles["BodyText"]))
    
    kolkata_time = datetime.now(ZoneInfo('Asia/Kolkata'))
    story.append(Paragraph(f"<b>Generated:</b> {kolkata_time.strftime('%d %b %Y, %H:%M')} (IST)", styles["BodyText"]))
    story.append(Spacer(1, 30))

    sections = [
        ("Flight Information", collected["flight_results"]),
        ("Hotel Information", collected["hotel_results"]),
        ("Research Results", collected["research_results"]),
        ("Final Travel Plan", collected["final_response"])
    ]

    # 3. Parse and Insert Content
    for title, text in sections:
        story.append(Paragraph(title, styles["SectionHeader"]))
        
        # Run the text through our custom markdown parser
        parsed_elements = parse_and_format_text(text, styles)
        story.extend(parsed_elements)
        
        story.append(Spacer(1, 15))

    doc.build(story)
    return pdf_path