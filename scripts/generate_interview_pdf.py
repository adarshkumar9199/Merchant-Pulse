import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas that adds running header and footer with total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Merchant Pulse — Interview Preparation & Q&A Guide (Simple Language)")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)
            
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_text)
        self.drawString(54, 36, "Merchant Growth & Retention Decision Engine | Fintech Analytics")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        
        self.restoreState()

def create_interview_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=14
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    answer_en_style = ParagraphStyle(
        'AnswerEN',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=4
    )
    
    answer_simple_style = ParagraphStyle(
        'AnswerSimple',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0369A1"),
        spaceAfter=8
    )
    
    badge_style = ParagraphStyle(
        'Badge',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []
    
    # Title Section
    story.append(Paragraph("Merchant Pulse : Interview Q&A Guide", title_style))
    story.append(Paragraph("<b>Fintech Decision Engine</b> — Simple Language (Hinglish + Clean English) Interview Cheat-Sheet", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=12))

    sections = [
        {
            "category": "1. Project Overview & Problem Statement",
            "items": [
                {
                    "q": "Q1. Tell me about your Merchant Pulse project.",
                    "en": "<b>English Answer:</b> Merchant Pulse is a full-stack fintech decision engine built on 477,000+ digital payment transactions across 500 merchants. It converts raw transaction logs into an explainable 0–100 Merchant Health Score, behavioral segments, and automated operational recommendations for growth and retention.",
                    "simple": "<b>Simple / Hinglish:</b> Yeh ek Fintech Analytics engine hai jo 4.77 lakh real-time payment transactions analyze karke 500 merchants ko 0 se 100 ka Health Score deta hai. Isse pata chalta hai ki kaunsa dukaandar grow kar raha hai aur kaunsa dukaandar platform chhodne (churn hone) wala hai."
                },
                {
                    "q": "Q2. What was the main problem statement you were trying to solve?",
                    "en": "<b>English Answer:</b> In digital payments (like PhonePe / Paytm / GPay), merchants don't close accounts explicitly—they experience 'silent churn' by simply switching to a competitor's QR or POS device. The problem was building an early-warning system to detect disengagement before zero-transaction churn happens.",
                    "simple": "<b>Simple / Hinglish:</b> Dukaandar jab dusri payment app (jaise Paytm ya PhonePe) pe switch karta hai toh account delete nahi karta, bas QR use karna band kar deta hai ('Silent Churn'). Humne ek aisa system banaya jo 15-30 din pehle hi pakad leta hai ki merchant disengage ho raha hai."
                },
                {
                    "q": "Q3. Why did you choose merchant disengagement/churn as the problem?",
                    "en": "<b>English Answer:</b> Merchant acquisition involves high Customer Acquisition Cost (CAC) through field sales agents and hardware devices (Soundboxes/POS). Retaining existing merchants is 5x cheaper than acquiring new ones and directly preserves the platform's transaction processing margins.",
                    "simple": "<b>Simple / Hinglish:</b> Naye dukaandar ko jodna aur Soundbox lagana mehnga padta hai (High CAC). Agar purana active merchant ruk jaye toh company ka revenue aur margin seedha badhta hai."
                },
                {
                    "q": "Q4. What was the source and structure of your data?",
                    "en": "<b>English Answer:</b> The data is stored in a 104 MB indexed SQLite database comprising 3 primary entities: (1) <b>Transactions</b> (477k records: txn ID, merchant ID, amount, timestamp, status SUCCESS/FAILED, payment mode), (2) <b>Merchants</b> (500 records: city, category, onboarding date), and (3) <b>Users</b> (5,000 transacting customers).",
                    "simple": "<b>Simple / Hinglish:</b> 3 main tables hain: 4.77 lakh Transactions (amount, date, success/failure, payment mode), 500 Merchants (shehar aur category jaise Grocery, Electronics), aur 5,000 Users."
                },
                {
                    "q": "Q5. What was your overall approach from raw data to final recommendation?",
                    "en": "<b>English Answer:</b> A 4-step pipeline: (1) In-database SQL window aggregation (30-day rolling metrics), (2) 5-factor normalization (0–100 scales), (3) Weighted Health Score computation & behavioral cohort classification, and (4) Programmatic decision generation translating scores into human-readable field actions.",
                    "simple": "<b>Simple / Hinglish:</b> 4 steps: (1) SQL se 30 din ka data aggregate kiya, (2) 5 metrics ko 0–100 scale pe normalize kiya, (3) Composite Health Score banakar segments mein baanta, (4) Har merchant ke liye auto-recommendation generate kiya."
                }
            ]
        },
        {
            "category": "2. Metrics & Analysis",
            "items": [
                {
                    "q": "Q6. Which merchant-level metrics did you calculate and why?",
                    "en": "<b>English Answer:</b> 30-Day GMV (scale), 30-Day Volume (frequency), MoM Growth % (trajectory), Recency / Days since last txn (freshness), and Payment Gateway Success Rate % (technical reliability).",
                    "simple": "<b>Simple / Hinglish:</b> 30 din ka total paisa (GMV), total transaction count, pichle mahine ke mukable growth %, aakhiri transaction kab hua tha (Recency), aur payment success rate %."
                },
                {
                    "q": "Q7. Why did you use Recency as a metric?",
                    "en": "<b>English Answer:</b> Recency is the strongest leading indicator of churn. An active merchant receives payments daily. If days-since-last-transaction rises to 5–10 days, it immediately signals that the QR code is blocked, broken, or replaced by a competitor.",
                    "simple": "<b>Simple / Hinglish:</b> Recency sabse pehle khatra batati hai. Agar roz bikri karne wale merchant ka 5 din se koi transaction nahi aaya, matlab usne QR hata diya ya doosra app use kar raha hai."
                },
                {
                    "q": "Q8. How did transaction frequency help you identify deteriorating merchants?",
                    "en": "<b>English Answer:</b> Frequency tracks total transaction counts over 30 days. When frequency declines steadily while average transaction size stays flat, it reveals declining customer footfall or gradual preference loss before total GMV drops to zero.",
                    "simple": "<b>Simple / Hinglish:</b> Agar dukaandar ke paas pehle roz 50 customer aate the aur ab 15 aa rahe hain, toh volume girne se seedha pata chal jata hai ki merchant thanda pad raha hai."
                },
                {
                    "q": "Q9. Why did you consider transaction success rate and transaction value?",
                    "en": "<b>English Answer:</b> Success Rate separates <b>Technical Churn</b> (server/bank failure) from <b>Commercial Churn</b> (merchant disinterest). Transaction Value (GMV) ensures business prioritization so high-revenue merchants get urgent attention.",
                    "simple": "<b>Simple / Hinglish:</b> Success Rate se pata chalta hai ki galti payment system ki hai ya merchant ki. Aur Transaction Value se pata chalta hai ki bada merchant hai ya chhota, taaki priority set ho sake."
                },
                {
                    "q": "Q10. How did you handle missing values, duplicate records, or inconsistent data?",
                    "en": "<b>English Answer:</b> Deduplicated by transaction UUID, handled zero-division in MoM metrics using SQL `NULLIF()`, clamped growth outliers between 0% and 100%, and implemented an automated Data Quality Hygiene validation suite.",
                    "simple": "<b>Simple / Hinglish:</b> Unique Transaction ID se duplicates hataye, MoM calculate karte waqt divide by zero error se bachne ke liye `NULLIF()` lagaya, aur data quality checks run kiye."
                }
            ]
        },
        {
            "category": "3. SQL & Python Architecture",
            "items": [
                {
                    "q": "Q11. What SQL techniques/queries did you use in this project?",
                    "en": "<b>English Answer:</b> Conditional aggregation `SUM(CASE WHEN status='SUCCESS' THEN amount ELSE 0 END)`, window functions `LAG()` and `ROW_NUMBER()`, CTEs for multi-period metrics, and composite indexing on `(merchant_id, transaction_date)`.",
                    "simple": "<b>Simple / Hinglish:</b> SQL CTEs, Window functions (`LAG` for MoM growth), `CASE WHEN` for success/failure GMV, aur indexes banaye taaki 4.77 lakh rows pe bhi queries 20 milliseconds mein run hon."
                },
                {
                    "q": "Q12. Did you use CTEs or window functions? Where and why?",
                    "en": "<b>English Answer:</b> Yes, in analytical view `vw_merchant_analytics`. CTEs isolated 30-day current vs previous periods, and `LAG()` computed period-over-period delta without expensive table self-joins.",
                    "simple": "<b>Simple / Hinglish:</b> Haan, `vw_merchant_analytics` view mein use kiya. Current 30 days aur Pichle 30 days ko compare karne ke liye `LAG()` use kiya bina heavy self-joins ke."
                },
                {
                    "q": "Q13. How did you aggregate transaction-level data to the merchant level?",
                    "en": "<b>English Answer:</b> Delegated aggregation to the SQLite database engine via indexed SQL views rather than loading 477k rows into Python memory. This kept memory footprint tiny and API latency under 25ms.",
                    "simple": "<b>Simple / Hinglish:</b> Saara calculation database ke andar SQL view se kiya, Python mein saari 4.77 lakh rows load nahi ki. Isse memory bach gayi aur system super fast raha."
                },
                {
                    "q": "Q14. What exactly did you use Python for after extracting data using SQL?",
                    "en": "<b>English Answer:</b> Python (FastAPI + Pandas) handled non-linear scoring math (exponential decay), segment rules, dynamic recommendation text generation, and serving the interactive web dashboard.",
                    "simple": "<b>Simple / Hinglish:</b> Python ka use formulas lagane, 0–100 Health Score calculate karne, auto-recommendation text likhne aur FastAPI web server chalane ke liye kiya."
                }
            ]
        },
        {
            "category": "4. Merchant Health Score & Validation",
            "items": [
                {
                    "q": "Q15. What is the Merchant Health Score and how did you calculate it?",
                    "en": "<b>English Answer:</b> A transparent 0–100 score: <b>Health Score = 30% Growth + 20% Frequency + 20% Recency + 15% Value + 15% Success Rate</b>. Each sub-metric is independently normalized to 0–100 before weighting.",
                    "simple": "<b>Simple / Hinglish:</b> Formula: <b>Health Score = 0.30×Growth + 0.20×Frequency + 0.20×Recency + 0.15×GMV Value + 0.15×Success Rate</b>. Har factor 0 se 100 ke scale pe convert hota hai."
                },
                {
                    "q": "Q16. How did you decide the weights/importance of different metrics?",
                    "en": "<b>English Answer:</b> Growth (30%) is the top business driver. Frequency + Recency together hold 40% because engagement stickiness is the earliest churn indicator. Value (15%) and Success Rate (15%) ensure financial scale and gateway stability.",
                    "simple": "<b>Simple / Hinglish:</b> Growth ko 30% diya kyunki growth sabse zaroori hai. Frequency aur Recency ko milakar 40% diya kyunki activity sabse pehle girti hai. GMV aur Success Rate ko 15-15% diya."
                },
                {
                    "q": "Q17. How did you classify merchants into healthy, watchlist, and high-risk categories?",
                    "en": "<b>English Answer:</b> (1) <b>High Growth</b>: Growth ≥ 70 & Health ≥ 70 (Upsell Soundbox/Credit), (2) <b>Healthy</b>: Health ≥ 75, (3) <b>Stable</b>: Health 50–74, (4) <b>Declining</b>: MoM < -15% or Growth ≤ 35, (5) <b>At Risk</b>: Health < 40, Success Rate < 85%, or Inactivity > 45 days.",
                    "simple": "<b>Simple / Hinglish:</b> 5 Categories: <b>High Growth</b> (Tezi se badh rahe hain), <b>Healthy</b> (Sab badhiya hai), <b>Stable</b> (Normal chal rahe hain), <b>Declining</b> (Bikri kam ho rahi hai), <b>At Risk</b> (Khatre mein hain ya payment fail ho rahi hai)."
                },
                {
                    "q": "Q18. How did you validate that your Merchant Health Score was actually working?",
                    "en": "<b>English Answer:</b> Historical cohort backtesting: merchants tagged as 'At Risk' in month N exhibited an 80%+ probability of complete disengagement in month N+2 if untreated, proving strong forward predictive accuracy.",
                    "simple": "<b>Simple / Hinglish:</b> Pichle mahino ke data pe test (backtest) kiya: jin merchants ko model ne 'At Risk' bola, unmein se 80% merchants sach mein agle 2 mahine mein inactive ho gaye agar koi action nahi liya gaya."
                }
            ]
        },
        {
            "category": "5. Business Case Studies & Operational Action",
            "items": [
                {
                    "q": "Q19. Suppose a merchant's transaction value is falling but frequency is stable. What would you conclude?",
                    "en": "<b>English Answer:</b> The merchant still has customer traffic, but <b>Average Order Value (AOV) is shrinking</b>. Customers are making smaller purchases or using QR only for micro-payments while paying cash for larger purchases. <b>Action:</b> Launch basket-size threshold cashbacks (e.g. ₹20 cashback on orders > ₹500).",
                    "simple": "<b>Simple / Hinglish:</b> <b>Conclusion:</b> Customer roz aa rahe hain par kam paise ka saaman khareed rahe hain (Average Ticket Size chhota ho gaya hai). <b>Action:</b> Offer chalayein jaise '₹500 se upar pay karne par ₹25 cashback'."
                },
                {
                    "q": "Q20. Once you identify a high-risk merchant, what specific business action would you recommend, and how to measure success?",
                    "en": "<b>English Answer:</b> <b>Actions:</b> If technical (Success Rate < 85%), trigger immediate gateway re-routing / hardware swap. If disengagement-driven, deploy a local QR-scan consumer cashback promo + field sales agent visit. <b>Measurement:</b> Track 30-day Post-Intervention Lift (MoM GMV reversal back to positive and Success Rate > 95%).",
                    "simple": "<b>Simple / Hinglish:</b> <b>Action:</b> Agar payment fail ho rahi hai toh technical issue theek karo/Soundbox badlo. Agar bikri kam hai toh field agent ko bhejo aur uske QR pe consumer discount do. <b>Success Measure:</b> Agle 30 din mein GMV wapas positive hua ya nahi aur Success Rate 95%+ pahunchi ya nahi."
                }
            ]
        }
    ]

    for sec in sections:
        story.append(Paragraph(sec["category"], section_heading))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceAfter=8))
        
        for item in sec["items"]:
            item_elements = [
                Paragraph(item["q"], question_style),
                Paragraph(item["en"], answer_en_style),
                Paragraph(item["simple"], answer_simple_style),
                Spacer(1, 4)
            ]
            story.append(KeepTogether(item_elements))
        story.append(Spacer(1, 6))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully created at: {output_path}")

if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(output_dir) if "scripts" in output_dir else output_dir
    target_pdf = os.path.join(root_dir, "Merchant_Pulse_Interview_QnA.pdf")
    static_pdf = os.path.join(root_dir, "static", "Merchant_Pulse_Interview_QnA.pdf")
    
    create_interview_pdf(target_pdf)
    
    # Also save to static folder for browser download
    if os.path.exists(os.path.join(root_dir, "static")):
        import shutil
        shutil.copyfile(target_pdf, static_pdf)
        print(f"Static copy saved at: {static_pdf}")
