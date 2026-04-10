# skill: health_insurance.md
# Domain knowledge for health insurance policy verification
# Used by verification_agent to identify misleading claims

## Purpose
Verify claims made by health insurance agents against actual policy documents.
Applies to individual health plans, family floater plans, group insurance, and top-up plans.

---

## Red Flags — Claims That Are Almost Always Misleading

- **"Covers everything"** → Always check the exclusions list. No policy covers everything.
- **"Cashless everywhere"** → Check the network hospital list. Cashless is only at empanelled hospitals.
- **"No waiting period"** → Check the waiting period schedule. Most policies have 30-day initial, 1-2 year for specific illnesses, 2-4 year for pre-existing conditions.
- **"Pre-existing conditions are covered from day one"** → Almost always false. Check Section on pre-existing disease (PED) waiting period.
- **"Full maternity cover"** → Check sub-limits and waiting period. Maternity usually has a 2-4 year waiting period and a fixed sub-limit.
- **"No co-payment"** → Check co-payment clause. Many policies have co-pay for senior citizens or specific treatments.
- **"Covers all hospitalization"** → Check for day-care procedures, room rent limits, and OPD exclusions.
- **"Claim will be settled in X days"** → Check actual claim settlement clause, not verbal promise.
- **"No room rent limit"** → Check room rent sub-limit clause. Many policies cap room rent at 1-2% of sum insured per day.
- **"Free health checkups included"** → Check frequency, which tests are covered, and whether it is cashless or reimbursement.

---

## Critical Clauses to Always Extract from Document

- **Exclusions list** — usually Section 3, 4, or Annexure
- **Waiting period schedule** — initial waiting period, specific illness waiting period, PED waiting period
- **Sub-limits table** — room rent, ICU charges, maternity, specific procedures
- **Network hospital clause** — how to find network hospitals, what happens at non-network
- **Co-payment clause** — percentage, conditions under which it applies
- **Restoration benefit clause** — if and how the sum insured is restored after a claim
- **No claim bonus (NCB)** — how it accumulates and whether it is protected
- **Free look period** — typically 15 days to return the policy
- **Claim process** — intimation timeline, documents required, settlement timeline
- **Day-care procedures list** — treatments covered without 24-hour hospitalization
- **OPD coverage** — whether outpatient consultations and medicines are covered

---

## Common Misleading Phrases Used by Agents

| What Agent Says | What to Actually Check |
|---|---|
| "Comprehensive coverage" | Check exclusions — comprehensive is marketing language |
| "Hassle-free claims" | Check claim process steps and document requirements |
| "Family floater covers everyone" | Check age limits for children and parents |
| "Sum insured gets restored" | Check restoration conditions — often only for unrelated illnesses |
| "Pre-existing covered after 2 years" | Check exact PED definition — pre-existing may be defined very broadly |
| "ICU is fully covered" | Check if ICU has a separate sub-limit |
| "Ayurveda and alternative treatment covered" | Check AYUSH sub-limit and which treatments qualify |
| "Ambulance charges covered" | Check the ambulance charge cap — often just ₹1,000-2,000 |

---

## Consumer Rights — India (IRDAI Guidelines)

- **Free Look Period**: 15 days from receipt of policy document to return without penalty
- **Claim Settlement Timeline**: Insurer must settle within 30 days of receiving all documents
- **Pre-authorization for Cashless**: Must be applied 48-72 hours before planned hospitalization; 24 hours for emergency
- **Grievance Redressal**: Insurer must respond within 15 days of complaint
- **Escalation**: IRDAI Bima Bharosa portal (bimabharosa.irdai.gov.in) for unresolved complaints
- **Ombudsman**: Insurance Ombudsman handles disputes up to ₹30 lakhs — free of charge
- **Portability**: Right to port policy to another insurer without losing waiting period credit (apply 45 days before renewal)

---

## Known High-Risk Exclusions Often Not Mentioned

- Injuries from adventure sports or hazardous activities
- Treatment outside India (unless international cover purchased)
- Dental treatment (unless specifically included)
- Vision/spectacles/contact lenses
- Cosmetic and plastic surgery (unless due to accident)
- Infertility and assisted reproduction
- Obesity treatment and bariatric surgery (unless specifically covered)
- Self-inflicted injuries
- War and nuclear perils
- Experimental treatments and unproven therapies
- Alcohol or drug-related conditions