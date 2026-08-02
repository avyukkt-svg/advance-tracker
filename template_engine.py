from typing import Dict

class TemplateEngine:
    def __init__(self):
        self.templates = {
            "Government Contract": {
                "what_happened": "The company has officially received a major order/contract.",
                "why_it_matters": "This contract significantly increases the company's order book and provides future revenue visibility.",
                "investment_impact": "Bullish",
                "impact_reason": "Direct positive impact on future earnings.",
                "next_steps": "Project execution will begin as per the contract timeline.",
                "risks": "Execution delays and working capital requirements."
            },
            "Dividend": {
                "what_happened": "The company's board has officially declared a dividend.",
                "why_it_matters": "The dividend declaration rewards shareholders and signals strong cash flow generation.",
                "investment_impact": "Bullish",
                "impact_reason": "Increases shareholder returns.",
                "next_steps": "Dividend will be paid to eligible shareholders on the record date.",
                "risks": "No material risks disclosed in the announcement."
            },
            "Bonus Issue": {
                "what_happened": "The company's board has approved a bonus issue of shares.",
                "why_it_matters": "A bonus issue increases liquidity in the stock and signals management's confidence in future growth.",
                "investment_impact": "Bullish",
                "impact_reason": "Improves stock liquidity and sentiment.",
                "next_steps": "Awaiting shareholder approval and fixing of the record date.",
                "risks": "Earnings per share (EPS) will be diluted proportionally."
            },
            "Stock Split": {
                "what_happened": "The company's board has approved a sub-division (split) of its equity shares.",
                "why_it_matters": "A stock split makes the shares more affordable to retail investors and increases liquidity.",
                "investment_impact": "Neutral",
                "impact_reason": "No change in fundamental valuation, but improves trading liquidity.",
                "next_steps": "Awaiting shareholder approval and fixing of the record date.",
                "risks": "No material risks disclosed in the announcement."
            },
            "Buyback": {
                "what_happened": "The company has approved a buyback of its equity shares.",
                "why_it_matters": "The buyback returns excess cash to shareholders and reduces the outstanding share count, boosting EPS.",
                "investment_impact": "Bullish",
                "impact_reason": "Increases earnings per share and supports the stock price.",
                "next_steps": "Awaiting regulatory clearances and fixing of the record date.",
                "risks": "Reduces cash reserves available for growth."
            },
            "Acquisition": {
                "what_happened": "The company has announced the acquisition of another entity or business division.",
                "why_it_matters": "This acquisition expands the company's market presence, product portfolio, or geographic reach.",
                "investment_impact": "Bullish",
                "impact_reason": "Inorganic growth that may lead to revenue synergies.",
                "next_steps": "Awaiting definitive agreements and regulatory approvals.",
                "risks": "Integration challenges and potential overvaluation of the target."
            },
            "Merger": {
                "what_happened": "The company has announced a merger or amalgamation scheme.",
                "why_it_matters": "The merger aims to consolidate operations, reduce costs, and create operational synergies.",
                "investment_impact": "Bullish",
                "impact_reason": "Long-term synergy benefits and scale expansion.",
                "next_steps": "Awaiting NCLT, shareholder, and creditor approvals.",
                "risks": "Significant regulatory hurdles and integration delays."
            },
            "USFDA Approval": {
                "what_happened": "The company has received an approval or clearance from the USFDA.",
                "why_it_matters": "This regulatory approval allows the company to launch new products in the highly lucrative US market.",
                "investment_impact": "Very Bullish",
                "impact_reason": "Directly unlocks new high-margin revenue streams.",
                "next_steps": "Commercial launch of the approved product in the US market.",
                "risks": "Market competition and pricing pressure."
            },
            "Quarterly Results": {
                "what_happened": "The company has officially announced its financial results.",
                "why_it_matters": "The financial results provide a comprehensive update on the company's revenue, profitability, and operational performance.",
                "investment_impact": "Neutral",
                "impact_reason": "Impact depends heavily on whether results beat or missed street estimates.",
                "next_steps": "Earnings call to discuss the results with analysts.",
                "risks": "Macroeconomic headwinds affecting margins."
            },
            "Management Change": {
                "what_happened": "The company has announced a key change in its management or board of directors.",
                "why_it_matters": "Leadership changes can signal strategic shifts, operational restructuring, or routine succession planning.",
                "investment_impact": "Neutral",
                "impact_reason": "Depends on the reputation of the incoming executive vs the outgoing one.",
                "next_steps": "The new appointee will assume responsibilities as per the effective date.",
                "risks": "Potential short-term operational disruption."
            },
            "Credit Rating": {
                "what_happened": "A credit rating agency has updated the company's credit rating.",
                "why_it_matters": "Credit ratings impact the company's borrowing costs and reflect its balance sheet strength.",
                "investment_impact": "Neutral",
                "impact_reason": "An upgrade lowers borrowing costs (bullish), while a downgrade increases them (bearish).",
                "next_steps": "No immediate corporate action required.",
                "risks": "Changes in debt servicing capabilities."
            }
        }

    def get_template(self, category: str) -> Dict[str, str]:
        return self.templates.get(category, {
            "what_happened": f"The company has made an announcement regarding {category}.",
            "why_it_matters": "This announcement provides a material update on corporate developments.",
            "investment_impact": "Neutral",
            "impact_reason": "Event requires further fundamental analysis.",
            "next_steps": "No immediate next steps disclosed.",
            "risks": "No material risks disclosed in the announcement."
        })
