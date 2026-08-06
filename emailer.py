import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from models import Announcement
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
        top_category = top_ann.ai_analysis.primary_event if top_ann.ai_analysis else "Unknown"

        subject = f"🚨 AI Analyst Alert | {top_ann.company} | {top_category} | Score: {top_ann.catalyst_score}/100"
        
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
        </style>
        </head>
        <body>
        <div class="container">
            <div class="header">
                <h1>NSE AI Equity Research Alert</h1>
            </div>
        """
        
        for ann in announcements:
            if not ann.ai_analysis:
                continue
                
            analysis = ann.ai_analysis
            
            # Routine Filings
            if ann.catalyst_score < 20:
                html_content += f"""
                <div class="routine-card">
                    <h3 style="margin-top: 0; color: #24292e;">{ann.company}</h3>
                    <p class="content-text" style="margin-bottom: 5px;"><strong>Document Type:</strong> {analysis.document_type}</p>
                    <p class="content-text" style="margin-bottom: 5px;"><strong>Importance:</strong> {analysis.market_importance}</p>
                    <p class="content-text" style="margin-bottom: 10px;"><strong>Summary:</strong> {analysis.one_sentence_summary}</p>
                    <a href="{ann.pdf_url}" style="color: #0366d6; text-decoration: none; font-size: 14px;">View PDF &rarr;</a>
                </div>
                """
                continue

            impact_class = "impact-neutral"
            if "Bullish" in analysis.investment_impact: impact_class = "impact-bullish"
            elif "Bearish" in analysis.investment_impact: impact_class = "impact-bearish"

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

            breakdowns = "".join([f"<li>{b.reason}: {b.points} pts</li>" for b in analysis.catalyst_score_breakdown])
            
            financials_html = ""
            f_dict = analysis.key_financial_numbers.model_dump()
            facts = [f"<strong>{k.replace('_', ' ').title()}:</strong> {v}" for k, v in f_dict.items() if v]
            if facts:
                financials_html = "<div class='key-facts'><ul>" + "".join([f"<li>{f}</li>" for f in facts]) + "</ul></div>"
            else:
                financials_html = "<p class='content-text'><em>No specific financial numbers extracted or validated.</em></p>"

            risks = "".join([f"<li><strong>{r.risk_type}:</strong> {r.explanation}</li>" for r in analysis.risk_analysis])
            opps = "".join([f"<li>{o}</li>" for o in analysis.opportunities])

            html_content += f"""
            <div class="card">
                <h2 class="card-title">{ann.company} | {analysis.primary_event}</h2>
                <table style="width: 100%; margin-bottom: 15px; font-size: 14px; color: #586069;">
                    <tr>
                        <td style="width: 50%;"><strong>Importance:</strong> {analysis.market_importance}</td>
                        <td style="width: 50%;"><strong>Document Type:</strong> {analysis.document_type}</td>
                    </tr>
                </table>
                
                <div class="section-title">EXECUTIVE SUMMARY</div>
                <p class="content-text">{analysis.executive_summary}</p>
                
                <div class="section-title">IMPORTANT NUMBERS</div>
                {financials_html}
                
                {price_table}
                
                <div class="section-title">INVESTMENT IMPACT</div>
                <p class="content-text"><span class="{impact_class}">{analysis.investment_impact}</span> &mdash; {analysis.investment_impact_explanation}</p>
                
                <div class="section-title">RISKS & OPPORTUNITIES</div>
                <p class="content-text" style="margin-bottom:5px;"><strong>Risks:</strong></p>
                <ul>{risks if risks else "<li>None identified</li>"}</ul>
                <p class="content-text" style="margin-bottom:5px; margin-top:10px;"><strong>Opportunities:</strong></p>
                <ul>{opps if opps else "<li>None identified</li>"}</ul>
                
                <div class="section-title">CATALYST SCORE: {analysis.catalyst_score}/100</div>
                <ul>{breakdowns}</ul>
                
                <a href="{ann.pdf_url}" class="btn" style="color: white !important;">View Source Document</a>
            </div>
            """

        html_content += """
            <div style="text-align: center; font-size: 12px; color: #959da5; margin-top: 30px;">
                Generated by NVIDIA Nemotron-3-Ultra (550b)
            </div>
        </div>
        </body>
        </html>
        """
        self._send(subject, html_content)

    def _send_empty_email(self):
        subject = "NSE AI Equity Research Alert: No Significant Announcements"
        html_content = "<p>No significant market-moving NSE announcements were detected by the AI Analyst.</p>"
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
