import datetime
from fpdf import FPDF

class WealthReportPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_color = (245, 176, 62)  # #f5b03e Gold
        self.text_dark = (33, 33, 33)        # #212121
        self.text_light = (102, 102, 102)    # #666666
        self.bg_light = (245, 245, 247)      # Light grey for table headers
        self.border_color = (220, 220, 220)  # Subtle grey border

    def header(self):
        # Draw a top decorative banner
        self.set_fill_color(*self.primary_color)
        self.rect(0, 0, 210, 4, "F")

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(*self.text_light)
        # Draw line
        self.set_draw_color(*self.border_color)
        self.line(10, self.get_y() - 2, 200, self.get_y() - 2)
        # Page numbers
        self.cell(0, 10, f"Page {self.page_no()} | BankNova AI Wealth Intelligence OS", 0, 0, "C")

def generate_pdf_report(report_data):
    pdf = WealthReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    
    # --- BRAND HEADER ---
    pdf.set_font("helvetica", "B", 24)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(10, 10, "B", ln=False)
    
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(*pdf.text_dark)
    pdf.cell(50, 10, "  BankNova AI", ln=False)
    
    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(*pdf.text_light)
    pdf.cell(0, 10, "Wealth Intelligence Report", ln=True, align="R")
    pdf.ln(5)
    
    # Thin divider line
    pdf.set_draw_color(*pdf.border_color)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    
    # --- METADATA SECTION ---
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(*pdf.text_dark)
    pdf.cell(30, 6, "Client Username:", ln=False)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(60, 6, str(report_data["user"]), ln=False)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(20, 6, "Date Generated:", ln=False)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, str(report_data["generated_at"]), ln=True, align="R")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(30, 6, "Email Address:", ln=False)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, str(report_data["email"]), ln=True)
    pdf.ln(8)
    
    # --- WEALTH SUMMARY ---
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 8, "WEALTH SUMMARY", ln=True)
    pdf.ln(2)
    
    summary = report_data["summary"]
    summary_items = [
        ("Total Wealth", f"Rs {summary['total_wealth']:,}" if isinstance(summary['total_wealth'], (int, float)) else str(summary['total_wealth'])),
        ("Savings Balance", f"Rs {summary['savings']:,}" if isinstance(summary['savings'], (int, float)) else str(summary['savings'])),
        ("Investments Portfolio", f"Rs {summary['investments']:,}" if isinstance(summary['investments'], (int, float)) else str(summary['investments'])),
        ("Emergency Fund Reserve", f"Rs {summary['emergency_fund']:,}" if isinstance(summary['emergency_fund'], (int, float)) else str(summary['emergency_fund'])),
        ("Monthly Income", f"Rs {summary['monthly_income']:,}" if isinstance(summary['monthly_income'], (int, float)) else str(summary['monthly_income'])),
        ("Monthly Expenses", f"Rs {summary['monthly_expenses']:,}" if isinstance(summary['monthly_expenses'], (int, float)) else str(summary['monthly_expenses'])),
        ("Monthly Savings Contribution", f"Rs {summary['monthly_savings']:,}" if isinstance(summary['monthly_savings'], (int, float)) else str(summary['monthly_savings'])),
        ("Savings Rate", str(summary['savings_rate']))
    ]
    
    # Table headers
    pdf.set_fill_color(*pdf.bg_light)
    pdf.set_draw_color(*pdf.border_color)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(*pdf.text_dark)
    pdf.cell(90, 7, "Metric Descriptor", border=1, fill=True)
    pdf.cell(90, 7, "Value", border=1, fill=True, ln=True)
    
    # Table rows
    pdf.set_font("helvetica", "", 9)
    for label, val in summary_items:
        pdf.cell(90, 7, f" {label}", border=1)
        pdf.cell(90, 7, f" {val}", border=1, ln=True)
    pdf.ln(8)
    
    # --- HEALTH SCORECARD ---
    health = report_data["financial_health_score"]
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 8, f"FINANCIAL HEALTH SCORECARD - {health['score']}/100 ({health['rating']})", ln=True)
    pdf.ln(2)
    
    # Pillars Table Headers
    pdf.set_fill_color(*pdf.bg_light)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(*pdf.text_dark)
    pdf.cell(90, 7, "Financial Health Pillar", border=1, fill=True)
    pdf.cell(90, 7, "Score Achieved", border=1, fill=True, ln=True)
    
    pdf.set_font("helvetica", "", 9)
    for pillar, score in health["pillars"].items():
        pillar_title = f" {pillar.replace('_', ' ').title()}"
        pdf.cell(90, 7, pillar_title, border=1)
        pdf.cell(90, 7, f" {score}/100", border=1, ln=True)
    pdf.ln(12)
    
    # --- DISCLAIMER ---
    pdf.set_font("helvetica", "I", 8)
    pdf.set_text_color(*pdf.text_light)
    pdf.multi_cell(0, 4.5, "Disclaimer: This report is generated automatically for educational purposes only and does not constitute licensed investment advice or professional financial planning under SEBI regulations. All evaluations and computations are based on self-reported inputs and standard calculations. Consult a registered financial advisor before making any investment decisions.")
    
    return pdf.output()
