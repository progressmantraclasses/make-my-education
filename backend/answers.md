# Answers

Verbatim, unedited output from `answer.py` for each of the 7 required questions.

---

## Question 1

**Query:** `I scored 78% and have a budget of ₹1.5 lakh/year — which engineering colleges can I consider?`

**Response:**

```json
{
  "answer": "Based on your 78% score and a budget of ₹1.5 lakh per academic year, you can consider the following engineering colleges in Uttarakhand:\n\n1. **Himalayan College of Engineering (C003)** – Cutoff is 75% (hard minimum) and the annual tuition fee is ₹132,000, which is within your budget. The college offers B.Tech programs in CSE, Civil, and EE.\n2. **Terai Technical University (C009)** – Cutoff is 70% (hard minimum) and the annual tuition fee is ₹118,000, also within your budget. It offers B.Tech programs in CSE and ME, as well as MCA and M.Tech.\n\nBoth institutions meet the minimum aggregate requirement and have tuition fees below ₹150,000 per year. No additional charges (hostel, mess, lab, etc.) are specified in the provided data, so the tuition fee is the primary cost to consider.\n\nColleges such as North Ridge Institute of Technology (C001) and Ambedkar National Institute (C012) have higher cutoff percentages (82% and 88% respectively) and therefore are not eligible for your score.",
  "citations": [
    "C003",
    "C009"
  ],
  "answered": true,
  "reason_if_unanswered": null
}
```

---

## Question 2

**Query:** `Which colleges offer an MBA, and what do they cost?`

**Response:**

```json
{
  "answer": "The colleges that offer an MBA are Doon Business School (C004) with an annual fee of ₹175,000 per academic year, and Ganga Valley University (C002) with an annual fee of ₹98,000 per academic year.",
  "citations": [
    "C004",
    "C002"
  ],
  "answered": true,
  "reason_if_unanswered": null
}
```

---

## Question 3

**Query:** `List the government colleges that have hostel facilities.`

**Response:**

```json
{
  "answer": "The government colleges in the provided data that have hostel facilities are Ambedkar National Institute (C012) and Kumaon Arts and Science College (C007). Both institutions are listed as Government type and indicate \"Hostel: Yes\" in their details.",
  "citations": [
    "C012",
    "C007"
  ],
  "answered": true,
  "reason_if_unanswered": null
}
```

---

## Question 4

**Query:** `What's the average placement package at North Ridge Institute of Technology?`

**Response:**

```json
{
  "answer": "The average placement package at North Ridge Institute of Technology (C001) is 6.5 LPA.",
  "citations": [
    "C001"
  ],
  "answered": true,
  "reason_if_unanswered": null
}
```

---

## Question 5

**Query:** `Does Ganga Valley University offer a PhD in Physics?`

**Response:**

```json
{
  "answer": "Ganga Valley University (C002) does not list a PhD in Physics among its offered programmes. The university’s listed courses are BBA, B.Com, BCA, and MBA, with no mention of doctoral programmes in physics or any other discipline.",
  "citations": [
    "C002"
  ],
  "answered": true,
  "reason_if_unanswered": null
}
```

---

## Question 6

**Query:** `Which colleges offer scholarships for students from low-income families?`

**Response:**

```json
{
  "answer": "Kumaon Arts and Science College (C007) provides means‑cum‑merit scholarships from the state government for students whose family income is below the eligibility threshold, covering tuition and a monthly stipend. None of the other colleges in the provided dataset mention scholarships specifically for low‑income families.",
  "citations": [
    "C007"
  ],
  "answered": true,
  "reason_if_unanswered": null
}
```

---

## Question 7

**Query:** `Which college is best for me? I have ₹1 lakh per semester.`

**Response:**

```json
{
  "answer": "Your budget of **₹1 lakh per semester** translates to **≈ ₹2 lakh per academic year** (assuming two equal semesters). Converting the annual fees of each college to a per‑semester figure gives:\n\n- **Ganga Institute of Commerce (C014)** – ₹72,000 / year → **≈ ₹36,000/semester**\n- **Kumaon Arts and Science College (C007)** – ₹15,000 / year → **≈ ₹7,500/semester**\n- **Ganga Valley University (C002)** – ₹98,000 / year → **≈ ₹49,000/semester**\n- **Ambedkar National Institute (C012)** – ₹45,000 / year → **≈ ₹22,500/semester**\n- Doon Business School (C004), Himalayan College of Engineering (C003), North Ridge Institute of Technology (C001) and Rishikesh Institute of Design (C008) exceed your budget (₹87,500 – ₹105,000/semester) and are therefore not viable options.\n\n### Colleges that fit your budget\n| College (ID) | Semester fee | Courses offered | Cut‑off (hard minimum) | Avg. placement* |\n|--------------|--------------|----------------|-----------------------|-----------------|\n| **Ganga Institute of Commerce** (C014) | ₹36,000 | B.Com, BBA, M.Com, CA‑Foundation | 63 % | 3.9 LPA |\n| **Kumaon Arts and Science College** (C007) | ₹7,500 | B.A, B.Sc, B.Com, M.A | 55 % | 2.8 LPA |\n| **Ganga Valley University** (C002) | ₹49,000 | BBA, B.Com, BCA, MBA | 68 % | 4.2 LPA |\n| **Ambedkar National Institute** (C012) | ₹22,500 | B.Tech, B.Arch, M.Tech | 88 % | 8.4 LPA |\n\n*Placement figures are average salary offers (LPA) reported by the institutions.\n\n### How to choose the \"best\" college for you\n1. **Field of interest** – If you want a commerce/management degree, the two dedicated commerce colleges (C014 and C002) are the natural choices. If you are interested in engineering or architecture, Ambedkar National Institute (C012) offers those programmes and also stays well within your budget.\n2. **Cut‑off requirement** – Your academic record must meet the hard‑minimum cut‑off. C012 has the highest bar (88 %), while C007 is the most accessible (55 %).\n3. **Placement prospects** – Among the budget‑friendly options, C012 shows the strongest placement average (8.4 LPA), followed by C002 (4.2 LPA) and C014 (3.9 LPA). C007 has the lowest placement average (2.8 LPA).\n4. **Overall recommendation** –\n   - **If you aim for a commerce/management career** and have a cut‑off around 65‑70 %, **Ganga Valley University (C002)** offers a good mix of relevant courses, a moderate cut‑off, and the second‑best placement average within your budget.\n   - **If you prefer a pure commerce focus** with a lower cut‑off, **Ganga Institute of Commerce (C014)** is also a solid, affordable option.\n   - **If you are qualified for a high cut‑off (≥ 88 %) and want engineering/architecture**, **Ambedkar National Institute (C012)** gives the best placement outcomes while still being well under your semester budget.\n\nChoose the college that aligns with your intended programme, meets your eligibility cut‑off, and offers the placement prospects you value most.",
  "citations": [
    "C014",
    "C007",
    "C002",
    "C012"
  ],
  "answered": true,
  "reason_if_unanswered": null
}
```

---
