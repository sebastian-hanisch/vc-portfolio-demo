"""PDF-Export des gewählten Startup-Portfolios (fpdf2, Helvetica-Kernfont)."""

import time


def generate_portfolio_pdf(label, result):
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Startup-Portfolio", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Methode: {label}  -  Erstellt: {time.strftime('%d.%m.%Y %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Zusammenfassung", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    summary_rows = [
        ("Erwarteter Portfolio-Wert", f"{result['expected_value']:.2f} Mio. EUR"),
        ("Investiertes Kapital", f"{result['total_ticket']:.2f} Mio. EUR"),
        ("Anzahl Deals", str(result["n_selected"])),
        ("Erwarteter Multiple", f"{result['expected_multiple']:.2f}x"),
        ("Sektoren belegt", str(len(result["sector_invested"]))),
    ]
    for label_text, value_text in summary_rows:
        pdf.cell(80, 7, label_text, border=0)
        pdf.cell(0, 7, value_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Ausgewählte Deals", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 9)
    headers = ["Deal", "Sektor", "Phase", "Ticket (Mio. EUR)", "Erw. Multiple"]
    widths = [35, 35, 30, 35, 35]
    pdf.set_fill_color(230, 230, 230)
    for header, width in zip(headers, widths):
        pdf.cell(width, 7, header, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(7)

    pdf.set_font("Helvetica", "", 9)
    for d in sorted(result["selected_deals"], key=lambda d: d.expected_value, reverse=True):
        row = [d.name, d.sector, d.stage, f"{d.ticket:.2f}", f"{d.expected_multiple:.2f}x"]
        for value, width in zip(row, widths):
            pdf.cell(width, 7, value, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(7)

    return bytes(pdf.output())
