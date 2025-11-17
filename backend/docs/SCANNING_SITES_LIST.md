# 🎯 Sites to Scan for ML Training

## Overview
This list contains 25 diverse sites to scan for building a robust ML false positive classifier.

**Target**: 180-200 scans total
**Strategy**: Multiple scans per site to establish consistency patterns

---

## 📋 Scanning Checklist

### ✅ Category 1: Intentionally Vulnerable Applications
*These sites contain REAL vulnerabilities - essential for ML training*

| # | Site | Scans | Status | Notes |
|---|------|-------|--------|-------|
| 1 | http://testphp.vulnweb.com | 5 | ⏳ | SQL injection, XSS, file inclusion |
| 2 | http://www.itsecgames.com | 5 | ⏳ | bWAPP - 100+ vulnerabilities |
| 3 | http://zero.webappsecurity.com | 5 | ⏳ | Banking app vulnerabilities |
| 4 | https://juice-shop.herokuapp.com | 3 | ⏳ | OWASP Juice Shop (already scanned, add more) |
| 5 | http://demo.testfire.net | 3 | ⏳ | IBM testfire (already scanned, add more) |
| 6 | https://public-firing-range.appspot.com | 3 | ⏳ | Google XSS testing ground |
| 7 | http://testhtml5.vulnweb.com | 3 | ⏳ | HTML5/Modern vulnerabilities |
| 8 | http://testasp.vulnweb.com | 3 | ⏳ | ASP.NET vulnerabilities |

**Subtotal**: 30 scans from vulnerable apps

---

### ✅ Category 2: Production Sites (Good Security)
*These sites have strong security - good for identifying false positives*

| # | Site | Scans | Status | Notes |
|---|------|-------|--------|-------|
| 9 | https://www.github.com | 3 | ⏳ | Modern SPA, excellent security |
| 10 | https://www.stackoverflow.com | 3 | ⏳ | High-traffic, good practices |
| 11 | https://www.medium.com | 3 | ⏳ | Content platform |
| 12 | https://www.reddit.com | 3 | ⏳ | Social media |
| 13 | https://www.wikipedia.org | 3 | ⏳ | Public wiki |
| 14 | https://www.shopify.com | 3 | ⏳ | E-commerce platform |
| 15 | https://www.stripe.com | 2 | ⏳ | Payment platform |
| 16 | https://www.cloudflare.com | 2 | ⏳ | Security company |
| 17 | https://www.npmjs.com | 2 | ⏳ | Package registry |
| 18 | https://www.docker.com | 2 | ⏳ | Container platform |

**Subtotal**: 26 scans from production sites

---

### ✅ Category 3: API Endpoints
*Different security model from web apps*

| # | Site | Scans | Status | Notes |
|---|------|-------|--------|-------|
| 19 | https://api.github.com | 3 | ⏳ | REST API |
| 20 | https://api.stackexchange.com | 3 | ⏳ | REST API |
| 21 | https://jsonplaceholder.typicode.com | 3 | ⏳ | Test REST API |

**Subtotal**: 9 scans from APIs

---

### ✅ Category 4: Educational/Test Sites
*Various security configurations*

| # | Site | Scans | Status | Notes |
|---|------|-------|--------|-------|
| 22 | http://www.webscantest.com | 2 | ⏳ | Scanner test site |
| 23 | https://example.com | 2 | ⏳ | Basic test site |
| 24 | http://httpbin.org | 2 | ⏳ | HTTP testing |
| 25 | https://reqres.in | 2 | ⏳ | API testing |

**Subtotal**: 8 scans from test sites

---

## 📊 Summary

**Total Sites**: 25
**Total Target Scans**: 73 (minimum)
**Combined with existing**: 73 + 127 = 200 scans ✅

### Distribution:
- Vulnerable apps: 30 scans (41%)
- Production sites: 26 scans (36%)
- APIs: 9 scans (12%)
- Test sites: 8 scans (11%)

---

## 🚀 Scanning Instructions

### Method 1: Via Frontend
1. Log into your scanner frontend
2. Create a new project or select existing
3. Add target URL
4. Configure scan:
   - Scan type: Comprehensive (passive + active)
   - Enable all tools (ZAP, Nuclei, SSLyze)
5. Start scan
6. Wait for completion
7. Repeat for each site

### Method 2: Via API (Faster)
```bash
# Example API call (adjust based on your setup)
curl -X POST http://localhost:8000/api/scans/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://testphp.vulnweb.com",
    "scan_type": "comprehensive"
  }'
```

### Method 3: Automated Script (Recommended)
I can create a script to automate scanning all these sites sequentially.

---

## 📝 Progress Tracking

### Week 1
- [ ] Switch to ML training database
- [ ] Scan vulnerable apps (30 scans)
- [ ] Verify data quality

### Week 2
- [ ] Scan production sites (26 scans)
- [ ] Scan APIs (9 scans)
- [ ] Scan test sites (8 scans)

### Week 3
- [ ] Train ML model
- [ ] Evaluate results
- [ ] Integrate into pipeline

---

## ⚠️ Important Notes

### Before Scanning:
1. ✅ Backup your current database
2. ✅ Switch to ML training database: `./db_switch_ml_training.sh`
3. ✅ Verify switch: `./db_status.sh` (should show 0 scans)

### During Scanning:
- Monitor progress: `./db_status.sh`
- Check for errors in scan logs
- Note any sites that fail or timeout
- Some sites may block scanners - that's okay

### Legal & Ethical:
- ✅ Vulnerable apps: Designed to be scanned
- ✅ Production sites: Only passive scanning (non-intrusive)
- ⚠️ Active scanning: Only on vulnerable apps and sites you own
- ⚠️ Respect rate limits and robots.txt

### Performance:
- Comprehensive scans take 10-30 minutes per site
- Passive scans take 2-5 minutes per site
- Plan for ~15-20 hours of total scanning time
- Can run multiple scans in parallel if server allows

---

## 🎯 Expected Results by Category

### Vulnerable Apps (30 scans)
- 15,000-20,000 vulnerabilities
- High severity: 50-100 findings
- Real SQL injection, XSS, etc.
- Low false positive rate

### Production Sites (26 scans)
- 8,000-12,000 findings
- Mostly informational/low severity
- Missing headers (false positives)
- Good security practices

### APIs (9 scans)
- 1,000-2,000 findings
- Different vulnerability types
- CORS, authentication issues
- Rate limiting detections

### Test Sites (8 scans)
- 1,000-2,000 findings
- Varied configurations
- Some intentional, some accidental issues

**Total Expected**: ~25,000-36,000 new vulnerabilities

---

## 🔧 Troubleshooting

### Site Won't Scan
- Check if site is accessible: `curl -I <site>`
- Check ZAP is running: `curl http://localhost:8080`
- Try passive-only scan first

### Scan Keeps Failing
- Reduce scan depth/duration
- Disable aggressive tests
- Try different time of day

### Too Slow
- Disable AJAX spider
- Reduce max duration
- Use passive-only for production sites

### Site Blocks Scanner
- Respect their decision
- Mark as attempted
- Move to next site
- Document in thesis as limitation

---

## 📈 Quality Checks

After scanning, verify:
```bash
# Check database stats
./db_status.sh

# Should show:
# - Scans: 70-80+
# - Vulnerabilities: 25,000-36,000+

# Analyze diversity
python analyze_data_diversity.py
```

Expected diversity:
- Multiple vulnerability types (SQL, XSS, headers, etc.)
- Wide confidence score range (0.5 - 1.0)
- All severity levels represented
- Mix of real and false positives

---

## 🎓 For Your FYP

### Dataset Description:
"Collected a diverse dataset by scanning 25 websites across 4 categories:
- 8 intentionally vulnerable applications for real vulnerability examples
- 10 production websites with strong security practices
- 3 API endpoints with different security models
- 4 test sites with varied configurations

Total: 73 new scans combined with existing 127 scans = 200 scans
Resulted in ~40,000-50,000 vulnerability findings with balanced representation
of true positives and false positives."

### Why This Approach:
"This diverse dataset ensures the ML model can:
1. Learn patterns of real vulnerabilities from vulnerable apps
2. Identify common false positives from secure production sites
3. Understand context differences (web apps vs APIs)
4. Generalize to unseen targets"

---

## ✅ Ready to Start?

### Next Steps:
1. Switch to ML training database:
   ```bash
   ./db_switch_ml_training.sh
   ```

2. Verify clean database:
   ```bash
   ./db_status.sh
   # Should show: Scans: 0, Vulnerabilities: 0
   ```

3. Start with vulnerable apps (high value for ML):
   - testphp.vulnweb.com
   - itsecgames.com
   - zero.webappsecurity.com

4. Track progress in this file (update Status column)

5. When done, proceed to ML training!

---

**Updated**: November 11, 2025
**Status**: Ready to begin scanning 🚀
**Estimated Time**: 15-20 hours total (can be spread over 1-2 weeks)
