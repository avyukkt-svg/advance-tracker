import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from models import Announcement
from template_engine import TemplateEngine
from utils import get_logger

logger = get_logger(__name__)

class Emailer:
    def __init__(self):
        self.server = Config.SMTP_SERVER
        self.port = Config.SMTP_PORT
        self.user = Config.SMTP_USER
        self.password = Config.SMTP_PASSWORD
        self.sender = Config.EMAIL_SENDER
        self.receiver = Config.EMAIL_RECEIVER
        self.template_engine = TemplateEngine()

    def send_email(self, announcements: list[Announcement]):
        if not self.user or not self.password or not self.receiver:
            logger.warning("Email credentials/receiver not configured. Skipping email.")
            return

        if not announcements:
            self._send_empty_email()
            return

        announcements.sort(key=lambda x: x.catalyst_score, reverse=True)
        announcements = announcements[:10]
        
        top_ann = announcements[0]
        top_category = top_ann.primary_event.category if top_ann.primary_event else top_ann.doc_type

        subject = f"🚨 High Catalyst NSE Alert | {top_ann.company} | {top_category} | Score: {top_ann.catalyst_score}/100"
        
        html_content = """
        <html>
        <head>
        <style>
            body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
            .header { border-bottom: 2px solid #002b5e; padding-bottom: 10px; margin-bottom: 20px; }
            .header h1 { color: #002b5e; font-size: 24px; margin: 0; }
            .card { border: 1px solid #e1e4e8; border-radius: 6px; padding: 20px; margin-bottom: 30px; background-color: #fafbfc; }
            .card-title { font-size: 20px; color: #0366d6; margin-top: 0; border-bottom: 1px solid #e1e4e8; padding-bottom: 10px; margin-bottom: 15px; }
            .table-prices { width: 100%; border-collapse: collapse; margin: 15px 0; background-color: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .table-prices th, .table-prices td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e1e4e8; }
            .table-prices th { background-color: #f6f8fa; font-weight: bold; color: #24292e; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }
            .table-prices td { font-size: 14px; font-weight: 500; color: #0366d6; }
            .section-title { font-size: 13px; font-weight: bold; color: #586069; text-transform: uppercase; margin-top: 20px; margin-bottom: 5px; letter-spacing: 1px; }
            .content-text { font-size: 15px; line-height: 1.6; margin-top: 0; margin-bottom: 15px; color: #24292e; }
            .key-facts { background-color: #f1f8ff; border-left: 4px solid #0366d6; padding: 10px 15px; margin: 15px 0; }
            .key-facts ul { margin: 0; padding-left: 20px; }
            .key-facts li { margin-bottom: 5px; font-size: 14px; }
            .impact-bullish { color: #28a745; font-weight: bold; }
            .impact-bearish { color: #d73a49; font-weight: bold; }
            .impact-neutral { color: #6a737d; font-weight: bold; }
            .btn { display: inline-block; background-color: #0366d6; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-size: 14px; font-weight: bold; margin-top: 15px; }
            .routine-card { border-left: 4px solid #6a737d; background-color: #f6f8fa; padding: 15px; margin-bottom: 15px; border-radius: 0 4px 4px 0; }
            .breakdown { font-size: 12px; color: #586069; margin-top: 5px; }
        </style>
        </head>
        <body>
        <div class="container">
            <div class="header">
                <h1>NSE Equity Research Alert</h1>
            </div>
        """
        
        for ann in announcements:
            # Format numbers
            breakdowns = "".join([f"<li>{b.reason}: {b.points} pts</li>" for b in ann.score_breakdown])
            
            importance = "Low"
            if ann.catalyst_score >= 70:
                importance = "Very High"
            elif ann.catalyst_score >= 30:
                importance = "Medium"
                
            # Routine Filings
            if not ann.primary_event or ann.catalyst_score < 20 or ann.doc_type in ["AGM Notice", "Board Meeting Notice", "Compliance Filing"]:
                html_content += f"""
                <div class="routine-card">
                    <h3 style="margin-top: 0; color: #24292e;">{ann.company}</h3>
                    <p class="content-text" style="margin-bottom: 5px;"><strong>Document Type:</strong> {ann.doc_type}</p>
                    <p class="content-text" style="margin-bottom: 5px;"><strong>Importance:</strong> Low</p>
                    <p class="content-text" style="margin-bottom: 10px;"><strong>Summary:</strong> This is a routine regulatory filing. No significant business event was announced.</p>
                    <a href="{ann.pdf_url}" style="color: #0366d6; text-decoration: none; font-size: 14px;">View PDF &rarr;</a>
                </div>
                """
                continue
                
            # Full Equity Research Block
            category = ann.primary_event.category
            evidence = ann.primary_event.evidence
            tmpl = self.template_engine.get_template(category)
            
            # Formulate Key Facts
            facts = []
            f_data = ann.extracted_financial_data or {}
            
            if f_data.get("order_values"): facts.append(f"<strong>Order Value:</strong> {', '.join(f_data['order_values'])}")
            if f_data.get("gov_agencies"): facts.append(f"<strong>Customer:</strong> {', '.join(f_data['gov_agencies'])}")
            if f_data.get("dividend_amounts"): facts.append(f"<strong>Dividend:</strong> {', '.join(f_data['dividend_amounts'])}")
            if f_data.get("revenue"): facts.append(f"<strong>Revenue:</strong> {', '.join(f_data['revenue'])}")
            if f_data.get("profit"): facts.append(f"<strong>Net Profit:</strong> {', '.join(f_data['profit'])}")
            if f_data.get("bonus_ratios"): facts.append(f"<strong>Bonus Ratio:</strong> {', '.join(f_data['bonus_ratios'])}")
            if f_data.get("split_ratios"): facts.append(f"<strong>Split Ratio:</strong> {', '.join(f_data['split_ratios'])}")
            if f_data.get("valid_dates"): facts.append(f"<strong>Relevant Date:</strong> {', '.join(f_data['valid_dates'][:1])}")
            
            facts_html = ""
            if facts:
                facts_html = "<div class='key-facts'><ul>" + "".join([f"<li>{f}</li>" for f in facts]) + "</ul></div>"
            else:
                facts_html = "<p class='content-text'><em>No specific financial numbers extracted.</em></p>"
                
            impact_class = "impact-neutral"
            if "Bullish" in tmpl['investment_impact']: impact_class = "impact-bullish"
            elif "Bearish" in tmpl['investment_impact']: impact_class = "impact-bearish"

            # Check if we successfully grabbed pricing data
            price_table = ""
            if hasattr(ann, 'current_price') and ann.current_price > 0:
                price_table = f"""
                <div class="section-title">MARKET CONTEXT & LEVELS</div>
                <table class="table-prices">
                    <tr>
                        <th>Current Price</th>
                        <th>Target Price</th>
                        <th>Support / Exit</th>
                        <th>Reliability</th>
                    </tr>
                    <tr>
                        <td>₹{ann.current_price:,.2f}</td>
                        <td>₹{ann.target_price:,.2f}</td>
                        <td>₹{ann.exit_price:,.2f}</td>
                        <td>{getattr(ann, 'reliability', 'High')}</td>
                    </tr>
                </table>
                <p style="font-size: 13px; color: #586069; margin-top: 5px;">Trend: {getattr(ann, 'trend', 'N/A')} | 52W High Distance: {getattr(ann, 'distance_to_52w_high', 0.0):.1f}% | 52W Low Distance: {getattr(ann, 'distance_to_52w_low', 0.0):.1f}%</p>
                """

            html_content += f"""
            <div class="card">
                <h2 class="card-title">{ann.company} | {category}</h2>
                <table style="width: 100%; margin-bottom: 15px; font-size: 14px; color: #586069;">
                    <tr>
                        <td style="width: 50%;"><strong>Importance:</strong> {importance}</td>
                        <td style="width: 50%;"><strong>Document Type:</strong> {ann.doc_type}</td>
                    </tr>
                </table>
                """
                
            # Render "Needs Manual Review" clearly if it was flagged by Primary Selector
            if category == "Needs Manual Review":
                html_content += f"""
                <div class="section-title" style="color: #d73a49;">NEEDS MANUAL REVIEW</div>
                <p class="content-text">{evidence}</p>
                <a href="{ann.pdf_url}" class="btn" style="background-color: #d73a49; color: white !important;">Review Source Document</a>
                </div>
                """
                continue
                
            # Standard Equity Research Alert
            html_content += f"""
                <div class="section-title">WHAT HAPPENED?</div>
                <p class="content-text">{tmpl['what_happened']}</p>
                
                <div class="section-title">WHY IT MATTERS</div>
                <p class="content-text">{tmpl['why_it_matters']}</p>
                
                <div class="section-title">IMPORTANT NUMBERS</div>
                {facts_html}
                
                {price_table}
                
                <div class="section-title">INVESTMENT IMPACT</div>
                <p class="content-text"><span class="{impact_class}">{tmpl['investment_impact']}</span> &mdash; {tmpl['impact_reason']}</p>
                
                <div class="section-title">NEXT STEPS</div>
                <p class="content-text">{tmpl['next_steps']}</p>
                
                <div class="section-title">EVIDENCE</div>
                <p class="content-text" style="font-style: italic; color: #6a737d;">"{evidence}"</p>
                
                <a href="{ann.pdf_url}" class="btn" style="color: white !important;">View Source Document</a>
            </div>
            """

        html_content += """
            <div style="text-align: center; font-size: 12px; color: #959da5; margin-top: 30px;">
                Generated by AI-Free Deterministic Scanner
            </div>
        </div>
        </body>
        </html>
        """
        self._send(subject, html_content)

    def _send_empty_email(self):
        subject = "NSE Equity Research Alert: No Significant Announcements"
        html_content = "<p>No significant market-moving NSE announcements were detected.</p>"
        self._send(subject, html_content)

    def _send(self, subject: str, html_content: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = self.receiver
            
            part = MIMEText(html_content, "html")
            msg.attach(part)
            
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.sender, [self.receiver], msg.as_string())
                
            logger.info(f"Email sent successfully to {self.receiver}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
