# Email Generator - Russell Brunson 7-Day Framework

A comprehensive Python-based email generation system that creates personalized, day-specific emails following Russell Brunson's proven 7-day email marketing framework.

## 🎯 Overview

This project generates professional grant funding emails for NGOs and social impact organizations using:
- **Russell Brunson's 7-Day Email Framework** (psychologically optimized sequences)
- **Dynamic personalization** (recipient names, organizations, grant amounts, deadlines)
- **Topic matching** (intelligent recipient-event pairing)
- **Engagement-based tone calibration** (adapts to recipient behavior)
- **Optional Groq AI** (for advanced generation)

## 📋 Features

### ✅ Email Generation Engine (`brain.py`)
- Day-specific email templates for all 7 days
- Deterministic fallback generation (works without API)
- Groq AI integration (optional, can be enabled)
- Recipient validation and topic matching
- Engagement score-based personalization
- Deadline checking and opt-out respect

### ✅ Seven Day Email Sequence

| Day | Type | Purpose | Tone |
|-----|------|---------|------|
| **0** | Registration Confirmation | Set expectations | Welcoming, Informative |
| **1** | Indoctrination | Create curiosity | Problem-focused, Engaging |
| **3** | Social Proof | Build credibility | Authoritative, Confident |
| **5** | Objection Handling | Address doubts | Empathetic, Logical |
| **6** | Final Push | Create urgency | Urgent, Motivating |
| **7a** | Morning Reminder | Prevent no-shows | High-energy, Supportive |
| **7b** | Final Warning | Last chance | Ultra-urgent, Direct |

### ✅ Email Storage System (`generate_sample_emails.py`)
- Organized folder structure by day
- Individual `.txt` files with full formatting
- JSON backups for programmatic access
- Master `INDEX.txt` with all emails
- Detailed `REPORT.txt` with statistics

### ✅ Sample Output
- **14 generated emails** (2 recipients × 7 days)
- **Fully personalized** with real data
- **Ready for immediate use or customization**

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/demonstrator669/email_generator.git
cd email_generator

# Install dependencies
pip install -r requirements.txt
```

### Generate Sample Emails

```bash
python3 generate_sample_emails.py
```

This creates a `sample_emails/` folder with organized emails by day.

### View Generated Emails

```bash
# View all emails index
cat sample_emails/INDEX.txt

# View specific day
ls sample_emails/day_1/

# View individual email
cat sample_emails/day_1/Aryan_Rawat_Women_in_Education_Grants_2025.txt
```

## 📁 Project Structure

```
email_generator/
├── brain.py                    # Main email generation engine
├── templates.py                # Russell Brunson framework templates
├── generate_sample_emails.py   # Email generation & storage system
├── run_first_email.py          # Multi-day email runner
├── requirements.txt            # Dependencies
├── .gitignore                  # Git configuration
├── DEPLOYMENT_SUMMARY.md       # Deployment documentation
├── README.md                   # This file
└── data/
    ├── recipients.json         # Recipient data (2 sample recipients)
    └── grant_events.json       # Grant events data (5 sample events)
```

## 🔧 Configuration

### Sample Data (data/recipients.json)

```json
[
  {
    "recipient_id": "r_001",
    "name": "Aryan Rawat",
    "email": "aryanrawat@example.com",
    "organization": "EduImpact Foundation",
    "topics": ["education", "women_empowerment"],
    "engagement_score": 0.72,
    "opt_out": false
  }
]
```

### Sample Events (data/grant_events.json)

```json
[
  {
    "event_id": "e_001",
    "title": "Women in Education Grants 2025",
    "tags": ["education", "women_empowerment"],
    "organizer": "Global Education Trust",
    "metadata": {
      "amount_range": "$10,000 - $50,000",
      "application_deadline": "2025-12-31"
    }
  }
]
```

## 🤖 Using Groq AI (Optional)

To enable AI-powered email generation:

1. **Get API Key**: https://console.groq.com/keys
2. **Set Environment Variable**:
   ```bash
   export GROQ_API_KEY="your-api-key-here"
   ```
3. **Install Package**:
   ```bash
   pip install groq
   ```
4. **Edit `generate_sample_emails.py` (line 115)**:
   ```python
   # Change from:
   brain.generate_batch(days=DAYS, use_ai=False)
   
   # To:
   brain.generate_batch(days=DAYS, use_ai=True)
   ```

## 📊 Sample Email Output

### Day 1 (Indoctrination)

**Subject:** The #1 mistake that kills 97% of Education applications

**Body:**
```
Hi Aryan Rawat,

In my work with EduImpact Foundation-like organizations, I see the same 
pattern over and over.

The #1 mistake that kills 97% of education applications isn't lack of 
merit. It's not even lack of funding sources.

It's applying to opportunities without understanding what funders actually 
want to see.

[... full email body ...]
```

## 🎨 Customization

### Add New Recipients
Edit `data/recipients.json`:
```json
{
  "recipient_id": "r_003",
  "name": "Your Name",
  "email": "email@example.com",
  "organization": "Your Organization",
  "topics": ["topic1", "topic2"],
  "engagement_score": 0.75,
  "opt_out": false
}
```

### Add New Events
Edit `data/grant_events.json`:
```json
{
  "event_id": "e_006",
  "title": "Your Grant Title",
  "tags": ["relevant_topics"],
  "organizer": "Organizer Name",
  "metadata": {
    "amount_range": "$X,000 - $Y,000",
    "application_deadline": "YYYY-MM-DD"
  }
}
```

### Customize Email Templates
Edit `templates.py` to modify:
- Subject line formulas
- Email structure
- Psychological principles
- Tone guidelines

## 📈 Generated Output Structure

```
sample_emails/
├── day_0/
│   ├── Aryan_Rawat_Women_in_Education_Grants_2025.txt
│   └── Nishi_Nayak_Green_Futures_Initiative_2025.txt
├── day_1/
│   ├── Aryan_Rawat_Women_in_Education_Grants_2025.txt
│   └── Nishi_Nayak_Green_Futures_Initiative_2025.txt
├── ... (days 3, 5, 6, 7a, 7b)
├── emails_day_0.json
├── emails_day_1.json
├── ... (JSON files for each day)
├── INDEX.txt          # Master index of all emails
└── REPORT.txt         # Detailed statistics and framework info
```

## 🔐 Validation & Safety

The system includes:
- ✅ Topic matching (only sends relevant emails)
- ✅ Opt-out checking (respects recipient preferences)
- ✅ Deadline validation (doesn't send expired opportunities)
- ✅ Required field validation (ensures data quality)
- ✅ Engagement score calibration (adapts tone)

## 📊 Statistics

- **Sample Emails Generated:** 14 (2 recipients × 7 days)
- **Matching Pairs:** Based on topic overlap
- **Blocked Emails:** Due to no topic match, opt-out, or deadline
- **Framework:** Russell Brunson's 7-Day Sequence

## 🚀 Deployment

### Export for Email Service

**As JSON:**
```bash
cat sample_emails/emails_day_1.json
```

**As CSV:**
```bash
# Emails are formatted as .txt files
# Can be imported into SendGrid, Mailgun, etc.
```

### Integration Examples

- **SendGrid:** Import JSON and use templates
- **Mailgun:** Use .txt files as email templates
- **Custom:** Parse JSON for any email service

## 📚 Documentation

- `DEPLOYMENT_SUMMARY.md` - Complete deployment guide
- `templates.py` - Email framework details
- `brain.py` - Generation engine documentation

## 🤝 Contributing

To add new features or improve the email templates:

1. Create a feature branch
2. Make your changes
3. Test with `python3 generate_sample_emails.py`
4. Submit a pull request

## 📝 License

This project is provided as-is for demonstration purposes.

## 🎯 Next Steps

1. **Customize Data:** Add your own recipients and events
2. **Generate Emails:** Run `python3 generate_sample_emails.py`
3. **Review:** Check the generated emails in `sample_emails/`
4. **Deploy:** Integrate with your email service
5. **Monitor:** Track open rates and engagement per day
6. **Optimize:** Refine based on performance metrics

## 📞 Support

For questions or issues:
- Check `DEPLOYMENT_SUMMARY.md`
- Review email generation logs
- Verify data format in `data/` folder

## 🔄 Version History

### v1.0 (Current)
- ✅ 7-day email framework
- ✅ Dynamic personalization
- ✅ Topic matching
- ✅ Engagement-based tone
- ✅ Sample email generation
- ✅ Multiple export formats

---

**Built with:** Python 3, Russell Brunson Framework, Groq AI  
**Status:** Production Ready  
**Last Updated:** 2025-11-12
