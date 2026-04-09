import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_DETAILS = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "jobshield_db")

client = AsyncIOMotorClient(MONGO_DETAILS)
db = client[DB_NAME]

async def seed_scam_templates():
    """
    Populates MongoDB with common scam patterns so the Vector Search
    actually works for your live demo.
    """
    templates = [
        # Laptop Security Deposit Scams (12 variants)
        {
            "text": "Pay INR 500 for laptop security deposit. This is refundable after 3 months of joining. Send payment to UPI amz@ybl.",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Laptop security deposit of INR 1000 required. Will be refunded after probation period. Contact HR at telegram @laptop_deposit",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "You need to deposit INR 800 as laptop security. This is company policy. Send via Google Pay to hr@company.co.in",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Refundable laptop deposit INR 1500. Must be paid before joining. Bank transfer to HDFC account: 1234567890",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Security deposit for laptop: INR 2000. Refundable after 6 months. Paytm transfer to 9876543210",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Company provides laptop but requires security deposit of Rs. 2500. Pay via UPI to hr@company",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Laptop deposit refundable after 3 months: Rs. 1000. Send via PhonePe to hr_recruiter123",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Need to pay INR 600 laptop security. Will be credited back after 90 days. UPI: secure@laptop",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Deposit for company laptop: 1500 rupees. Non-refundable if you leave before 6 months. Pay to HR",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Laptop security fee Rs. 1200. Transfer to Axis Bank account ending 5678. Receipt required.",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Refundable deposit Rs. 900 for laptop. Pay through UPI id: jobs@paytm. Mention your name.",
            "scam_type": "Laptop Security Scam"
        },
        {
            "text": "Company laptop security deposit: INR 750. Pay now to confirm your joining. Google Pay: 98765xxxxx",
            "scam_type": "Laptop Security Scam"
        },

        # Processing/Registration Fee Scams (12 variants)
        {
            "text": "Urgent hiring for Amazon. Salary 45000. No interview. Just pay processing fee of 999. Apply on telegram @amazonjobs_desk.",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Processing fee Rs. 1500 required to process your offer letter. Pay via UPI to hr@flipkartjobs",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Registration charge of Rs. 500. Non-refundable. Pay to get your appointment letter. Telegram: @hr_register",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Document verification fee: Rs. 800. Pay to verify your credentials. PhonePe: 98765xxxxx",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Pay Rs. 1200 as onboarding fee. This includes background check. Bank transfer to ICICI xxxx1234",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Service charge Rs. 999 for job placement. Refundable if not placed. WhatsApp: +91 98765xxxxx",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Processing charge: Rs. 2000. Pay to activate your profile. Google Pay to hr@companyportal",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Offer letter processing fee: Rs. 600. Transfer to account 4567891234. HDFC Bank.",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Admin fee Rs. 750 to release your joining letter. Pay via Paytm to 98765xxxxx",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Training fee Rs. 2500. Will be adjusted in your salary. Pay now to start. UPI: training@jobs",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Security verification deposit: Rs. 1000. Refundable after 1 month. Telegram: @verifyjobs",
            "scam_type": "Fee for Offer Scam"
        },
        {
            "text": "Appointment letter fee Rs. 500. Pay via Google Pay to get your letter. Number: 98765xxxxx",
            "scam_type": "Fee for Offer Scam"
        },

        # Urgent Hiring/Short Deadline Scams (10 variants)
        {
            "text": "URGENT! Limited time offer. Apply now or miss this opportunity. Last date today. Contact @urgent_hiring",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "Immediate joining required. Salary 60000 per month. Last chance to apply. WhatsApp: +91 98765xxxxx",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "Hire Immediately - 50 positions open. Last 2 hours to apply. Call now: 9876543210",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "Apply within 2 hours or position will be filled. No interview required. Telegram: @fasttrackjobs",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "Emergency hiring for WFH positions. Salary 50000. Only today. Pay processing to secure spot.",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "Only 5 slots left! Apply now or miss forever. Call HR at 98765xxxxx for immediate joining.",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "Walk-in interview today. Last chance. Salary 55000. Bring documents and pay registration fee.",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "TOMORROW DEADLINE! Don't miss this opportunity. Immediate appointment. Contact: @deadlinejobs",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "Hurry! Limited time. 10000 salary per month. Pay deposit to reserve your position now!",
            "scam_type": "Urgent Hiring Scam"
        },
        {
            "text": "Apply NOW! This offer expires in 1 hour. No interview. Start tomorrow. Telegram: @nowhiring",
            "scam_type": "Urgent Hiring Scam"
        },

        # Data Theft/Aadhaar/PAN Scams (10 variants)
        {
            "text": "Government job alert! Earn 5000 per day by clicking links. No experience required. Send Aadhaar and PAN copy to proceed.",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "Verify your identity: Send Aadhaar card copy to hr@company.in to process offer.",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "Need copy of PAN card and bank details for salary account. Email to hr@recruiter.com",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "Submit Aadhaar number and photo ID for background verification. WhatsApp: +91 98765xxxxx",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "Share passport size photo and ID proof to get your appointment letter. Telegram: @doc_submission",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "Upload your Aadhaar, PAN, and bank passbook for salary processing. Website: www.company-jobs.in",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "Send scanned copies of all ID documents including driving license. Email: apply@company.co",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "KYC verification required: Send Aadhaar card front and back. Also share OTP for verification.",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "Need your date of birth, address proof, and photo ID for employee verification. Submit now.",
            "scam_type": "Data Theft Scam"
        },
        {
            "text": "Complete your profile: Upload Aadhaar, PAN, and 6-month bank statements. Telegram: @profile_verify",
            "scam_type": "Data Theft Scam"
        },

        # Telegram/WhatsApp Scams (10 variants)
        {
            "text": "Join our Telegram channel for job updates: t.me/amazoncareers. Pay membership fee to access premium jobs.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "WhatsApp group for jobs: +91-9876543210. Pay Rs. 300 to join. Get daily job alerts.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "Telegram: @TechMahindraJobs - Pay Rs. 500 to get interview schedule. Limited seats.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "Join WhatsApp: +91 98765xxxxx for WFH jobs. Pay monthly subscription Rs. 200.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "Telegram channel for government jobs: t.me/govtjobs123. Pay activation fee Rs. 1000.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "Message @recruiter123 on Telegram to apply. Pay consultation fee Rs. 750.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "WhatsApp now: +91 98765xxxxx for part-time jobs. Earn 5000 daily. Pay to start.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "Telegram: @instant_jobs - Pay Rs. 299 for immediate placement. No experience needed.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "Add WhatsApp +91 98765xxxxx for data entry jobs. Pay security deposit Rs. 500.",
            "scam_type": "Telegram Scam"
        },
        {
            "text": "Telegram group: t.me/jobalert2024. Pay Rs. 1500 for premium access. Guaranteed job.",
            "scam_type": "Telegram Scam"
        },

        # Fake Company/Interview Scams (6 variants)
        {
            "text": "Congratulations! You have been selected. Pay security deposit to confirm. ICICI Bank transfer: xxxx5678",
            "scam_type": "Fake Interview Scam"
        },
        {
            "text": "You are selected! Pay Rs. 2000 for onboarding documents. Telegram: @selected_hr",
            "scam_type": "Fake Interview Scam"
        },
        {
            "text": "Your interview is cleared. Pay Rs. 1500 to receive offer letter. Google Pay: 98765xxxxx",
            "scam_type": "Fake Interview Scam"
        },
        {
            "text": "Selected for WFH job. Pay refundable deposit Rs. 1000. Bank transfer to HDFC: 1234567890",
            "scam_type": "Fake Interview Scam"
        },
        {
            "text": "Offer letter will be sent after payment of Rs. 800. Pay via Paytm to 98765xxxxx",
            "scam_type": "Fake Interview Scam"
        },
        {
            "text": "Congratulations on selection! Pay Rs. 1200 for training materials. UPI: training@jobs123",
            "scam_type": "Fake Interview Scam"
        }
    ]

    # Insert templates
    await db.scam_templates.delete_many({})
    await db.scam_templates.insert_many(templates)
    print(f"✅ Seeded {len(templates)} Scam Templates.")


async def seed_threat_intel():
    """
    Populates a blacklist of known scam identifiers.
    """
    intel = [
        # UPI IDs (20 entries)
        {"identifier": "amz@ybl", "type": "upi", "severity": "critical", "category": "job_scam", "source": "community_report"},
        {"identifier": "amazonjobs@ybl", "type": "upi", "severity": "critical", "category": "job_scam", "source": "platform_check"},
        {"identifier": "hr@flipkart", "type": "upi", "severity": "high", "category": "impersonation", "source": "community_report"},
        {"identifier": "jobs@paytm", "type": "upi", "severity": "high", "category": "job_scam", "source": "platform_check"},
        {"identifier": "secure@laptop", "type": "upi", "severity": "high", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "training@jobs", "type": "upi", "severity": "critical", "category": "advance_fee", "source": "known_scammer"},
        {"identifier": "hr@companyportal", "type": "upi", "severity": "high", "category": "job_scam", "source": "community_report"},
        {"identifier": "verify@jobs", "type": "upi", "severity": "high", "category": "data_theft", "source": "platform_check"},
        {"identifier": "deposit@laptop", "type": "upi", "severity": "critical", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "registration@jobs", "type": "upi", "severity": "high", "category": "advance_fee", "source": "community_report"},
        {"identifier": "processing@fees", "type": "upi", "severity": "critical", "category": "advance_fee", "source": "platform_check"},
        {"identifier": "offer@letter", "type": "upi", "severity": "high", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "hr@recruiter", "type": "upi", "severity": "high", "category": "impersonation", "source": "community_report"},
        {"identifier": "apply@company", "type": "upi", "severity": "medium", "category": "job_scam", "source": "platform_check"},
        {"identifier": "jobs@consultant", "type": "upi", "severity": "high", "category": "advance_fee", "source": "known_scammer"},
        {"identifier": "pay@security", "type": "upi", "severity": "critical", "category": "job_scam", "source": "community_report"},
        {"identifier": "deposit@refund", "type": "upi", "severity": "high", "category": "job_scam", "source": "platform_check"},
        {"identifier": "onboarding@fee", "type": "upi", "severity": "critical", "category": "advance_fee", "source": "known_scammer"},
        {"identifier": "document@verify", "type": "upi", "severity": "high", "category": "data_theft", "source": "community_report"},
        {"identifier": "profile@activation", "type": "upi", "severity": "high", "category": "job_scam", "source": "platform_check"},

        # Telegram handles (15 entries)
        {"identifier": "amazonjobs_desk", "type": "telegram", "severity": "critical", "category": "job_scam", "source": "platform_check"},
        {"identifier": "laptop_deposit", "type": "telegram", "severity": "high", "category": "job_scam", "source": "community_report"},
        {"identifier": "hr_register", "type": "telegram", "severity": "high", "category": "advance_fee", "source": "known_scammer"},
        {"identifier": "urgent_hiring", "type": "telegram", "severity": "high", "category": "job_scam", "source": "platform_check"},
        {"identifier": "fasttrackjobs", "type": "telegram", "severity": "high", "category": "job_scam", "source": "community_report"},
        {"identifier": "deadlinejobs", "type": "telegram", "severity": "high", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "nowhiring", "type": "telegram", "severity": "high", "category": "job_scam", "source": "platform_check"},
        {"identifier": "doc_submission", "type": "telegram", "severity": "critical", "category": "data_theft", "source": "community_report"},
        {"identifier": "profile_verify", "type": "telegram", "severity": "critical", "category": "data_theft", "source": "known_scammer"},
        {"identifier": "amazoncareers", "type": "telegram", "severity": "critical", "category": "impersonation", "source": "platform_check"},
        {"identifier": "techmahindrajobs", "type": "telegram", "severity": "critical", "category": "impersonation", "source": "community_report"},
        {"identifier": "govtjobs123", "type": "telegram", "severity": "high", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "instant_jobs", "type": "telegram", "severity": "critical", "category": "job_scam", "source": "platform_check"},
        {"identifier": "jobalert2024", "type": "telegram", "severity": "high", "category": "job_scam", "source": "community_report"},
        {"identifier": "selected_hr", "type": "telegram", "severity": "critical", "category": "job_scam", "source": "known_scammer"},

        # Phone numbers (15 entries)
        {"identifier": "9876543210", "type": "phone", "severity": "critical", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "9876512345", "type": "phone", "severity": "high", "category": "job_scam", "source": "community_report"},
        {"identifier": "9876523456", "type": "phone", "severity": "high", "category": "job_scam", "source": "platform_check"},
        {"identifier": "9876534567", "type": "phone", "severity": "high", "category": "advance_fee", "source": "known_scammer"},
        {"identifier": "9876545678", "type": "phone", "severity": "critical", "category": "job_scam", "source": "community_report"},
        {"identifier": "9876556789", "type": "phone", "severity": "high", "category": "data_theft", "source": "platform_check"},
        {"identifier": "9876567890", "type": "phone", "severity": "high", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "9876578901", "type": "phone", "severity": "critical", "category": "job_scam", "source": "community_report"},
        {"identifier": "9876589012", "type": "phone", "severity": "high", "category": "impersonation", "source": "platform_check"},
        {"identifier": "9876590123", "type": "phone", "severity": "high", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "9876501234", "type": "phone", "severity": "critical", "category": "job_scam", "source": "community_report"},
        {"identifier": "9876512340", "type": "phone", "severity": "high", "category": "advance_fee", "source": "platform_check"},
        {"identifier": "9876523451", "type": "phone", "severity": "high", "category": "job_scam", "source": "known_scammer"},
        {"identifier": "9876534562", "type": "phone", "severity": "critical", "category": "data_theft", "source": "community_report"},
        {"identifier": "9876545673", "type": "phone", "severity": "high", "category": "job_scam", "source": "platform_check"}
    ]

    await db.threat_intel.delete_many({})
    await db.threat_intel.insert_many(intel)
    print(f"✅ Seeded {len(intel)} Threat Intel Identifiers.")


async def main():
    await seed_scam_templates()
    await seed_threat_intel()

if __name__ == "__main__":
    asyncio.run(main())